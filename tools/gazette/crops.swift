// Renders many crops of PDF pages in one run, to read them by eye or to review readings.
// Reads JSON lines on stdin, one crop each:
//   {"pdf": "sources/joradp/A2026025.pdf", "page": 6, "x": 0.5, "y": 0.25, "w": 0.45, "h": 0.08,
//    "out": "crop.png", "dpi": 220}
// where x, y, w and h are fractions of the page, y from the top, as ocr.swift prints them.
//
// macOS only (PDFKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/crops.swift < crops.jsonl
import AppKit
import Foundation
import PDFKit

var docs: [String: PDFDocument] = [:]
while let line = readLine() {
    guard let data = line.data(using: .utf8),
          let d = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let path = d["pdf"] as? String, let number = d["page"] as? Int, let out = d["out"] as? String,
          let x = d["x"] as? Double, let y = d["y"] as? Double, let w = d["w"] as? Double, let h = d["h"] as? Double
    else {
        FileHandle.standardError.write("bad line: \(line)\n".data(using: .utf8)!)
        exit(1)
    }
    if docs[path] == nil { docs[path] = PDFDocument(url: URL(fileURLWithPath: path)) }
    guard let page = docs[path]?.page(at: number - 1) else {
        FileHandle.standardError.write("no page \(number) in \(path)\n".data(using: .utf8)!)
        exit(1)
    }
    let box = page.bounds(for: .mediaBox)
    let crop = CGRect(x: box.minX + x * box.width, y: box.maxY - (y + h) * box.height,
                      width: w * box.width, height: h * box.height)
    let scale = CGFloat((d["dpi"] as? Double) ?? 200) / 72
    let pw = Int(crop.width * scale), ph = Int(crop.height * scale)
    let ctx = CGContext(data: nil, width: pw, height: ph, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: pw, height: ph))
    ctx.scaleBy(x: scale, y: scale)
    ctx.translateBy(x: -crop.minX, y: -crop.minY)
    page.draw(with: .mediaBox, to: ctx)
    let rep = NSBitmapImageRep(cgImage: ctx.makeImage()!)
    try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
}
