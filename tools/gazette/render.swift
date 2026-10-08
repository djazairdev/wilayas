// Renders part of a PDF page as a PNG, to read the printed gazette by eye.
//
// macOS only (PDFKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/render.swift file.pdf page x y width height out.png [dpi]
//   (x, y, width and height in PDF points from the page's bottom-left corner)
import AppKit
import Foundation
import PDFKit

let a = CommandLine.arguments
guard a.count >= 8, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])),
      let page = doc.page(at: Int(a[2])! - 1) else {
    FileHandle.standardError.write("usage: render.swift file.pdf page x y width height out.png [dpi]\n".data(using: .utf8)!)
    exit(1)
}
let crop = CGRect(x: Double(a[3])!, y: Double(a[4])!, width: Double(a[5])!, height: Double(a[6])!)
let scale = CGFloat(a.count > 8 ? Double(a[8])! : 200) / 72
let w = Int(crop.width * scale), h = Int(crop.height * scale)
let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                    space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
ctx.scaleBy(x: scale, y: scale)
ctx.translateBy(x: -crop.minX, y: -crop.minY)
page.draw(with: .mediaBox, to: ctx)
let rep = NSBitmapImageRep(cgImage: ctx.makeImage()!)
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: a[7]))
