package main

import (
	"code.google.com/p/go-tour/pic"
    "fmt"
	"math/rand"
	"image"
    "image/color"
)

// http://tour.golang.org/#60

type Pixel struct{ R, G, B uint8 }
type Image struct{ Data [][]Pixel }

func (img Image) ColorModel() color.Model {
	return color.RGBAModel
}

func (img Image) Bounds() image.Rectangle {
	return image.Rect(
        0,
        0,
        len(img.Data),
        len(img.Data[0]))
}

func (img Image) At(x, y int) color.Color {
    return color.RGBA{
        img.Data[x][y].R,
        img.Data[x][y].G,
        img.Data[x][y].B,
        255,
    }
}

func RandomPixel() Pixel {
	return Pixel{
		uint8(rand.Intn(256)),
		uint8(rand.Intn(256)),
		uint8(rand.Intn(256)),
	}
}

func RandomImage(w, h int) Image {
	data := make([][]Pixel, w)
	for i := 0; i < w; i++ {
		data[i] = make([]Pixel, h)
		for j := 0; j < h; j++ {
			data[i][j] = RandomPixel()
		}
	}
	return Image{data}
}

func main() {
	m := RandomImage(100, 100)

    for i := 0; i < 3; i++ {
        for j := 0; j < 3; j++ {
            fmt.Printf("%-4d", m.Data[i][j])
        }
        fmt.Print("\n")
    }

	pic.ShowImage(m)
}
