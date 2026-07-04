from __future__ import annotations

import dataclasses
import functools
import glob
import math
import concurrent.futures
import pathlib
import re
import shutil
import subprocess
import tempfile
import time
from collections import OrderedDict

import click
from PIL import Image, ImageChops, ImageOps, ImageStat

try:
	import pillow_heif
except ImportError:  # pragma: no cover - optional at runtime
	pillow_heif = None


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif", ".heic", ".heif"}
BLOG_ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIC_ROOT = BLOG_ROOT / "static"
ATTACHMENT_REF_RE = re.compile(r"(?P<prefix>/?)embeds/books/attachments/(?P<name>[^)\"'`\s<>]+?)\.(?P<ext>png|jpg|jpeg)")


@dataclasses.dataclass(slots=True)
class Candidate:
	path: pathlib.Path
	format: str
	size_bytes: int
	rms_error: float
	description: str


@dataclasses.dataclass(slots=True)
class OptimizationResult:
	source: pathlib.Path
	best_candidate: Candidate | None
	original_size: int
	best_candidate_data: bytes | None = None
	skipped_reason: str | None = None


def register_heif() -> None:
	if pillow_heif is not None:
		pillow_heif.register_heif_opener()


def is_animated(image: Image.Image) -> bool:
	return bool(getattr(image, "is_animated", False)) and getattr(image, "n_frames", 1) > 1


def image_has_transparency(image: Image.Image) -> bool:
	if image.mode in {"RGBA", "LA"}:
		alpha = image.getchannel("A")
		return alpha.getextrema()[0] < 255

	if image.mode == "P" and "transparency" in image.info:
		return True

	return False


def reference_image(image: Image.Image) -> Image.Image:
	return ImageOps.exif_transpose(image).convert("RGBA")


def apply_max_width(image: Image.Image, max_width: int | None) -> tuple[Image.Image, bool]:
	if max_width is None or max_width <= 0 or image.width <= max_width:
		return image, False

	scale = max_width / image.width
	new_height = max(1, round(image.height * scale))
	return image.resize((max_width, new_height), Image.Resampling.LANCZOS), True


def rms_error(reference: Image.Image, candidate_path: pathlib.Path) -> float:
	with Image.open(candidate_path) as candidate_image:
		candidate = ImageOps.exif_transpose(candidate_image).convert("RGBA")

	if candidate.size != reference.size:
		candidate = candidate.resize(reference.size, Image.Resampling.LANCZOS)

	diff = ImageChops.difference(reference, candidate)
	stats = ImageStat.Stat(diff)
	return math.sqrt(sum(value * value for value in stats.rms) / len(stats.rms))


def save_png_variants(image: Image.Image, reference: Image.Image, temp_dir: pathlib.Path, use_optipng: bool) -> list[Candidate]:
	candidates: list[Candidate] = []

	base_image = image
	if image.mode not in {"RGB", "RGBA", "P", "L", "LA"}:
		base_image = image.convert("RGBA" if image_has_transparency(image) else "RGB")

	lossless_path = temp_dir / "candidate-lossless.png"
	base_image.save(lossless_path, format="PNG", optimize=True, compress_level=9)
	if use_optipng:
		run_optipng(lossless_path)
	candidates.append(
		Candidate(
			path=lossless_path,
			format="png",
			size_bytes=lossless_path.stat().st_size,
			rms_error=rms_error(reference, lossless_path),
			description="png-lossless",
		)
	)

	quantize_source = base_image.convert("RGBA" if image_has_transparency(base_image) else "RGB")
	for colors in (256, 192, 128, 96, 64):
		quantized = quantize_source.quantize(colors=colors)
		candidate_path = temp_dir / f"candidate-{colors}.png"
		quantized.save(candidate_path, format="PNG", optimize=True, compress_level=9)
		if use_optipng:
			run_optipng(candidate_path)
		candidates.append(
			Candidate(
				path=candidate_path,
				format="png",
				size_bytes=candidate_path.stat().st_size,
				rms_error=rms_error(reference, candidate_path),
				description=f"png-{colors}",
			)
		)

	return candidates


def save_jpeg_variants(
	image: Image.Image,
	reference: Image.Image,
	temp_dir: pathlib.Path,
	max_rms_error: float,
) -> list[Candidate]:
	if image_has_transparency(image):
		return []

	rgb_image = image.convert("RGB")

	for quality in (60, 65, 70, 75, 80, 85, 90, 95):
		candidate_path = temp_dir / f"candidate-{quality}.jpg"
		rgb_image.save(
			candidate_path,
			format="JPEG",
			quality=quality,
			optimize=True,
			progressive=True,
			subsampling="4:2:0",
		)
		candidate = Candidate(
			path=candidate_path,
			format="jpg",
			size_bytes=candidate_path.stat().st_size,
			rms_error=rms_error(reference, candidate_path),
			description=f"jpeg-{quality}",
		)
		if candidate.rms_error <= max_rms_error:
			return [candidate]

	return []


def run_optipng(path: pathlib.Path) -> None:
	result = subprocess.run(
		["optipng", "-o7", "-quiet", str(path)],
		capture_output=True,
		text=True,
	)
	if result.returncode != 0:
		raise RuntimeError(f"optipng failed for {path}: {result.stderr.strip()}")


def choose_best_candidate(
	source: pathlib.Path,
	original_size: int,
	candidates: list[Candidate],
	max_rms_error: float,
	allow_format_change: bool,
	min_savings_ratio: float,
	force_apply: bool,
) -> Candidate | None:
	acceptable = [candidate for candidate in candidates if candidate.rms_error <= max_rms_error]
	if not acceptable:
		return None

	acceptable.sort(key=lambda candidate: (candidate.size_bytes, candidate.rms_error))
	for candidate in acceptable:
		savings_ratio = (original_size - candidate.size_bytes) / original_size
		if savings_ratio < 0:
			continue
		if not force_apply and savings_ratio < min_savings_ratio:
			continue
		if candidate.path.suffix.lower() != source.suffix.lower() and not allow_format_change:
			continue
		return candidate

	return None


def optimize_image(
	path: pathlib.Path,
	max_rms_error: float,
	allow_format_change: bool,
	use_optipng: bool,
	min_savings_ratio: float,
	max_width: int | None,
) -> OptimizationResult:
	register_heif()
	original_size = path.stat().st_size

	with Image.open(path) as image:
		if is_animated(image):
			return OptimizationResult(source=path, best_candidate=None, original_size=original_size, skipped_reason="animated")

		image.load()
		working_image = ImageOps.exif_transpose(image)
		working_image, resized_for_width = apply_max_width(working_image, max_width)
		reference = reference_image(working_image)

	with tempfile.TemporaryDirectory(prefix="image-opt-") as temp_dir_name:
		temp_dir = pathlib.Path(temp_dir_name)
		candidates = []
		candidates.extend(save_png_variants(working_image, reference, temp_dir, use_optipng))
		candidates.extend(save_jpeg_variants(working_image, reference, temp_dir, max_rms_error))

		best_candidate = choose_best_candidate(
			path,
			original_size,
			candidates,
			max_rms_error,
			allow_format_change,
			min_savings_ratio,
			resized_for_width,
		)
		if best_candidate is None:
			return OptimizationResult(source=path, best_candidate=None, original_size=original_size, skipped_reason="no-smaller-acceptable-candidate")

		candidate_data = best_candidate.path.read_bytes()
		return OptimizationResult(
			source=path,
			best_candidate=Candidate(
				path=best_candidate.path,
				format=best_candidate.format,
				size_bytes=best_candidate.size_bytes,
				rms_error=best_candidate.rms_error,
				description=best_candidate.description,
			),
			original_size=original_size,
			best_candidate_data=candidate_data,
		)


def optimize_worker(
	path: pathlib.Path,
	max_rms_error: float,
	allow_format_change: bool,
	use_optipng: bool,
	min_savings_ratio: float,
	max_width: int | None,
) -> tuple[pathlib.Path, OptimizationResult | None, str | None]:
	try:
		result = optimize_image(
			path,
			max_rms_error=max_rms_error,
			allow_format_change=allow_format_change,
			use_optipng=use_optipng,
			min_savings_ratio=min_savings_ratio,
			max_width=max_width,
		)
		return path, result, None
	except Exception as exc:
		return path, None, str(exc)


def iter_images(directory: pathlib.Path, recursive: bool) -> list[pathlib.Path]:
	iterator = directory.rglob("*") if recursive else directory.glob("*")
	return sorted(path for path in iterator if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS)


def expand_inputs(target: str, recursive: bool) -> list[pathlib.Path]:
	target_path = pathlib.Path(target)
	paths: list[pathlib.Path] = []

	if target_path.exists():
		if target_path.is_dir():
			paths.extend(iter_images(target_path, recursive))
		elif target_path.is_file() and target_path.suffix.lower() in SUPPORTED_EXTENSIONS:
			paths.append(target_path)
	else:
		if glob.has_magic(target):
			for match in glob.glob(target, recursive=recursive):
				match_path = pathlib.Path(match)
				if match_path.is_dir():
					paths.extend(iter_images(match_path, recursive))
				elif match_path.is_file() and match_path.suffix.lower() in SUPPORTED_EXTENSIONS:
					paths.append(match_path)

	# De-duplicate while preserving stable order.
	return sorted(dict.fromkeys(path.resolve() for path in paths))


def build_replacements(old_path: pathlib.Path, new_path: pathlib.Path) -> OrderedDict[str, str]:
	replacements: OrderedDict[str, str] = OrderedDict()

	def add(old: str, new: str) -> None:
		if old and old != new:
			replacements[old] = new

	old_abs = old_path.resolve().as_posix()
	new_abs = new_path.resolve().as_posix()
	add(old_abs, new_abs)

	try:
		old_repo_rel = old_path.resolve().relative_to(BLOG_ROOT).as_posix()
		new_repo_rel = new_path.resolve().relative_to(BLOG_ROOT).as_posix()
		add(old_repo_rel, new_repo_rel)
		if old_repo_rel.startswith("static/") and new_repo_rel.startswith("static/"):
			old_public_rel = old_repo_rel[len("static/"):]
			new_public_rel = new_repo_rel[len("static/"):]
			add(f"/{old_public_rel}", f"/{new_public_rel}")
			add(old_public_rel, new_public_rel)
	except ValueError:
		pass

	try:
		old_static_rel = old_path.resolve().relative_to(STATIC_ROOT).as_posix()
		new_static_rel = new_path.resolve().relative_to(STATIC_ROOT).as_posix()
		add(f"/{old_static_rel}", f"/{new_static_rel}")
		add(old_static_rel, new_static_rel)
	except ValueError:
		pass

	return replacements


def rewrite_paths(search_root: pathlib.Path, renames: list[tuple[pathlib.Path, pathlib.Path]]) -> tuple[int, int]:
	replacements: OrderedDict[str, str] = OrderedDict()
	for old_path, new_path in renames:
		for old_text, new_text in build_replacements(old_path, new_path).items():
			replacements[old_text] = new_text

	files_updated = 0
	replacements_applied = 0
	for path in search_root.rglob("*"):
		if not path.is_file():
			continue

		try:
			original_text = path.read_text(encoding="utf-8")
		except (UnicodeDecodeError, OSError):
			continue

		updated_text = original_text
		# Also heal stale extension references where old extension no longer exists
		# but the alternate extension exists in static/.
		for match in ATTACHMENT_REF_RE.finditer(original_text):
			prefix = match.group("prefix")
			name = match.group("name")
			ext = match.group("ext")
			old_ref = f"{prefix}embeds/books/attachments/{name}.{ext}"
			alt_ext = "jpg" if ext == "png" else "png"
			new_ref = f"{prefix}embeds/books/attachments/{name}.{alt_ext}"

			old_static = STATIC_ROOT / f"embeds/books/attachments/{name}.{ext}"
			new_static = STATIC_ROOT / f"embeds/books/attachments/{name}.{alt_ext}"
			if (not old_static.exists()) and new_static.exists():
				replacements.setdefault(old_ref, new_ref)

		for old_text, new_text in replacements.items():
			count = updated_text.count(old_text)
			if count:
				replacements_applied += count
				updated_text = updated_text.replace(old_text, new_text)

		if updated_text != original_text:
			path.write_text(updated_text, encoding="utf-8")
			files_updated += 1

	return files_updated, replacements_applied


def apply_result(result: OptimizationResult) -> pathlib.Path | None:
	if result.best_candidate is None or result.best_candidate_data is None:
		return None

	target_path = result.source.with_suffix(f".{result.best_candidate.format}")
	temp_target = target_path.with_suffix(f"{target_path.suffix}.tmp-opt")
	temp_target.write_bytes(result.best_candidate_data)
	shutil.copystat(result.source, temp_target)
	temp_target.replace(target_path)
	if target_path != result.source:
		result.source.unlink()
	return target_path


def format_bytes(size: int) -> str:
	units = ["B", "KB", "MB", "GB"]
	value = float(size)
	for unit in units:
		if value < 1024 or unit == units[-1]:
			return f"{value:.1f}{unit}"
		value /= 1024
	return f"{value:.1f}GB"


def format_options(
	target: str,
	apply_changes: bool,
	recursive: bool,
	largest_first: bool,
	max_rms_error: float,
	min_savings_ratio: float,
	max_width: int | None,
	jobs: int,
	allow_format_change: bool,
	rewrite_paths_in: pathlib.Path | None,
	use_optipng: bool,
) -> str:
	return (
		"OPTIONS "
		f"target={target} "
		f"apply={apply_changes} "
		f"recursive={recursive} "
		f"largest_first={largest_first} "
		f"max_rms_error={max_rms_error} "
		f"min_savings={min_savings_ratio} "
		f"max_width={max_width if max_width is not None else 'none'} "
		f"jobs={jobs} "
		f"allow_format_change={allow_format_change} "
		f"rewrite_paths_in={rewrite_paths_in if rewrite_paths_in is not None else 'none'} "
		f"use_optipng={use_optipng}"
	)


def precompute_sizes(paths: list[pathlib.Path], progress_every: int = 500) -> dict[pathlib.Path, int]:
	sizes: dict[pathlib.Path, int] = {}
	total = len(paths)
	for index, path in enumerate(paths, 1):
		sizes[path] = path.stat().st_size
		if index % progress_every == 0 or index == total:
			click.echo(f"SIZE_PROGRESS {index}/{total}")
	return sizes


def flush_rewrites(search_root: pathlib.Path, renames: list[tuple[pathlib.Path, pathlib.Path]], batch_index: int) -> tuple[int, int]:
	if not renames:
		return 0, 0
	files_updated, replacements_applied = rewrite_paths(search_root, renames)
	click.echo(
		f"REWRITE_BATCH {batch_index} root={search_root} files={files_updated} replacements={replacements_applied} renames={len(renames)}"
	)
	return files_updated, replacements_applied


@click.command()
@click.argument("target", type=str)
@click.option("--apply", "apply_changes", is_flag=True, help="Write optimized files back to disk.")
@click.option("--recursive/--no-recursive", default=True, show_default=True, help="Recurse through subdirectories.")
@click.option("--largest-first/--no-largest-first", default=False, show_default=True, help="Process larger files before smaller ones.")
@click.option("--max-rms-error", default=6.0, show_default=True, type=float, help="Maximum per-pixel RMS error allowed for a candidate.")
@click.option("--min-savings", "min_savings_ratio", default=0.0, show_default=True, type=float, help="Minimum fractional size savings required to apply a change (0.1 = 10%).")
@click.option("--max-width", default=None, type=int, help="Resize images wider than this many pixels before encoding candidates.")
@click.option("--jobs", default=1, show_default=True, type=int, help="Number of images to optimize in parallel.")
@click.option("--allow-format-change", is_flag=True, help="Allow png<->jpg conversion. Use with care because paths will change.")
@click.option("--rewrite-paths-in", default=None, type=click.Path(exists=True, file_okay=False, path_type=pathlib.Path), help="If a file is renamed, replace old paths with new paths under this directory.")
@click.option("--use-optipng/--no-optipng", default=shutil.which("optipng") is not None, show_default=True, help="Use optipng for PNG candidates when available.")
def main(
	target: str,
	apply_changes: bool,
	recursive: bool,
	largest_first: bool,
	max_rms_error: float,
	min_savings_ratio: float,
	max_width: int | None,
	jobs: int,
	allow_format_change: bool,
	rewrite_paths_in: pathlib.Path | None,
	use_optipng: bool,
) -> None:
	"""Find smaller acceptable image encodings for TARGET.

	TARGET can be a directory, a single image file, or a glob pattern.
	"""
	if min_savings_ratio < 0 or min_savings_ratio >= 1:
		raise click.BadParameter("--min-savings must be in the range [0, 1).")
	if max_width is not None and max_width <= 0:
		raise click.BadParameter("--max-width must be a positive integer.")
	if jobs <= 0:
		raise click.BadParameter("--jobs must be a positive integer.")

	click.echo(
		format_options(
			target,
			apply_changes,
			recursive,
			largest_first,
			max_rms_error,
			min_savings_ratio,
			max_width,
			jobs,
			allow_format_change,
			rewrite_paths_in,
			use_optipng,
		)
	)

	register_heif()
	click.echo("DISCOVER resolving target to image list...")
	discovery_start = time.perf_counter()
	paths = expand_inputs(target, recursive)
	discovery_elapsed = time.perf_counter() - discovery_start
	if not paths:
		click.echo("No supported images found for target.")
		return
	click.echo(f"DISCOVER found {len(paths)} image(s) in {discovery_elapsed:.2f}s")

	click.echo("SIZE scanning file sizes...")
	size_start = time.perf_counter()
	sizes = precompute_sizes(paths)
	size_elapsed = time.perf_counter() - size_start
	click.echo(f"SIZE completed in {size_elapsed:.2f}s")

	if largest_first:
		click.echo("SORT largest-first enabled; sorting by descending size...")
		sort_start = time.perf_counter()
		paths = sorted(paths, key=lambda path: sizes[path], reverse=True)
		sort_elapsed = time.perf_counter() - sort_start
		click.echo(f"SORT completed in {sort_elapsed:.2f}s")

	total_before = sum(sizes[path] for path in paths)
	total_after = 0
	optimized_count = 0
	skipped_count = 0
	renames: list[tuple[pathlib.Path, pathlib.Path]] = []
	rewrite_files_updated_total = 0
	rewrite_replacements_total = 0
	rewrite_batch_index = 0
	rewrite_batch_size = 100

	worker = functools.partial(
		optimize_worker,
		max_rms_error=max_rms_error,
		allow_format_change=allow_format_change,
		use_optipng=use_optipng,
		min_savings_ratio=min_savings_ratio,
		max_width=max_width,
	)

	if jobs == 1:
		results = map(worker, paths)
	else:
		executor = concurrent.futures.ThreadPoolExecutor(max_workers=jobs)
		results = executor.map(worker, paths)

	try:
		total_files = len(paths)
		for index, (path, result, error) in enumerate(results, 1):
			progress = f"[{index}/{total_files}]"
			if error is not None or result is None:
				skipped_count += 1
				click.echo(f"{progress} SKIP {path}: {error}")
				continue

			if result.best_candidate is None:
				skipped_count += 1
				total_after += result.original_size
				click.echo(f"{progress} KEEP {path}: {result.skipped_reason}")
				continue

			savings = result.original_size - result.best_candidate.size_bytes
			percent = 100 * savings / result.original_size
			click.echo(
				f"{progress} BEST {path}: {result.best_candidate.description} "
				f"{format_bytes(result.original_size)} -> {format_bytes(result.best_candidate.size_bytes)} "
				f"({percent:.1f}% saved, rms={result.best_candidate.rms_error:.2f})"
			)

			optimized_count += 1
			total_after += result.best_candidate.size_bytes

			if apply_changes:
				target_path = apply_result(result)
				if target_path is not None and target_path != path:
					renames.append((path, target_path))
					click.echo(f"{progress} RENAME {path} -> {target_path}")
					if rewrite_paths_in is not None and len(renames) >= rewrite_batch_size:
						rewrite_batch_index += 1
						files_updated, replacements_applied = flush_rewrites(rewrite_paths_in, renames, rewrite_batch_index)
						rewrite_files_updated_total += files_updated
						rewrite_replacements_total += replacements_applied
						renames.clear()
	finally:
		if jobs != 1:
			executor.shutdown(wait=True)

	if apply_changes and rewrite_paths_in is not None:
		if renames:
			rewrite_batch_index += 1
			files_updated, replacements_applied = flush_rewrites(rewrite_paths_in, renames, rewrite_batch_index)
			rewrite_files_updated_total += files_updated
			rewrite_replacements_total += replacements_applied
			renames.clear()
		click.echo(
			f"REWRITE_SUMMARY root={rewrite_paths_in} files={rewrite_files_updated_total} replacements={rewrite_replacements_total} batches={rewrite_batch_index}"
		)

	click.echo(
		f"SUMMARY files={len(paths)} optimized={optimized_count} kept={skipped_count} "
		f"size={format_bytes(total_before)} -> {format_bytes(total_after)}"
	)
	if not apply_changes:
		click.echo("Dry run only. Re-run with --apply to write optimized files.")


if __name__ == "__main__":
	main()