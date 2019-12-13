package main

import (
    "io"
    "os"
    "strings"
)

type rot13Reader struct {
    wrappedReader io.Reader
}

charMap := make(map[char]char)
for c := 'A'; c <= 'M'; c++ {
	charMap[c] = c + 13
}

func (r *rot13Reader) Read(p []byte) (n int, err error) {
	buf := make([]byte, len(p))
	bytes, err := r.wrappedReader.Read(buf)
	if err == nil {
		for i := 0; i < bytes; i++ {
			if (buf[i] >= 65 && buf[i] < 65 + 13) || (buf[i] >= 97 && buf[i] < 97 + 13) {
				p[i] = buf[i] + 13
			} else if (buf[i] >= 65 + 13 && buf[i] < 65 + 26) || (buf[i] >= 97 + 13 && buf[i] < 97 + 26) {
				p[i] = buf[i] - 13
			} else {
				p[i] = buf[i]
			}

		}

	}
	return bytes, err
}

func main() {
    s := strings.NewReader("Lbh penpxrq gur pbqr!\n")
    r := rot13Reader{s}
    io.Copy(os.Stdout, &r)
}
