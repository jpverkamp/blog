{{- $title := or (.Get "title") (.Get 0) -}}
{{- $text := or (.Get "text") (.Get "title") (.Get 0) -}}

{{- $.Scratch.Set "written" false -}}

{{- range $page := .Site.AllPages -}}
    {{- if (and (not ($.Scratch.Get "written")) (eq $page.Title $title)) -}}
        <a href="{{ $page.Permalink }}">{{ $text }}</a>
        {{- $.Scratch.Set "written" true -}}
    {{- end -}}
{{- end -}}

{{- range $page := .Site.AllPages -}}
    {{- if (and (not ($.Scratch.Get "written")) (in $page.Title $title)) -}}
        <a href="{{ $page.Permalink }}">{{ $text }}</a>
        {{- $.Scratch.Set "written" true -}}
    {{- end -}}
{{- end -}}

{{- if (not ($.Scratch.Get "written")) -}}
{{ errorf "Failed to generate crosslink for title: %q, text: %q" $title $text }}
{{- end -}}