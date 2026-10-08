// Reads regions of pages with OCR (Apple's Vision framework), like ocr.swift does whole pages.
// The OCR of a whole page loses a line here and there; reading each column, or each row of a
// table, on its own finds most of them again. Reads JSON lines on stdin, one region each:
//   {"pdf": "sources/joradp/A1991041.pdf", "page": 4, "x": 0.0, "y": 0.087, "w": 0.5595, "h": 0.0596,
//    "dpi": 300, "lang": "ar-SA"}
// where x, y, w and h are fractions of the page, y from the top, and prints one JSON line per line
// of text with its position on the page, as ocr.swift does.
//
// macOS only (PDFKit, Vision). Used once, to transcribe the gazette; the build doesn't need it.
//
//   python3 tools/gazette/regions.py columns ar work/A1991041.ocr.jsonl | swift tools/gazette/regions.swift > work/A1991041.columns.ocr.jsonl
import Foundation
import PDFKit
import Vision

func json(_ s: String) -> String {
    let data = try! JSONSerialization.data(withJSONObject: [s], options: [])
    return String(String(data: data, encoding: .utf8)!.dropFirst().dropLast())
}

var docs: [String: PDFDocument] = [:]
while let line = readLine() {
    guard let data = line.data(using: .utf8),
          let d = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let path = d["pdf"] as? String, let number = d["page"] as? Int,
          let rx = d["x"] as? Double, let ry = d["y"] as? Double, let rw = d["w"] as? Double, let rh = d["h"] as? Double
    else {
        FileHandle.standardError.write("bad line: \(line)\n".data(using: .utf8)!)
        exit(1)
    }
    let dpi = CGFloat(d["dpi"] as? Double ?? 300), lang = d["lang"] as? String ?? "ar-SA"
    if docs[path] == nil { docs[path] = PDFDocument(url: URL(fileURLWithPath: path)) }
    guard let page = docs[path]?.page(at: number - 1) else {
        FileHandle.standardError.write("no page \(number) in \(path)\n".data(using: .utf8)!)
        exit(1)
    }
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72
    let w = Int(box.width * scale * CGFloat(rw)), h = Int(box.height * scale * CGFloat(rh))
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    // move the region's bottom-left corner to the origin
    ctx.translateBy(x: -(box.minX + CGFloat(rx) * box.width), y: -(box.minY + CGFloat(1 - ry - rh) * box.height))
    page.draw(with: .mediaBox, to: ctx)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = [lang]
    request.usesLanguageCorrection = false
    try! VNImageRequestHandler(cgImage: ctx.makeImage()!, options: [:]).perform([request])
    for o in request.results ?? [] {
        guard let c = o.topCandidates(1).first else { continue }
        let b = o.boundingBox
        let x = rx + Double(b.minX) * rw, y = ry + Double(1 - b.maxY) * rh
        print("{\"page\":\(number),\"x\":\(x),\"y\":\(y),\"w\":\(Double(b.width) * rw),\"h\":\(Double(b.height) * rh),\"conf\":\(c.confidence),\"text\":\(json(c.string))}")
    }
}
