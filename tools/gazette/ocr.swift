// Reads printed text with OCR (Apple's Vision framework) and prints one JSON line per
// line of text, with its position: x, y, w and h are fractions of the page, y from the top.
// Used for the scanned 1984 gazette, and for the Arabic of the later issues, whose
// embedded text PDFKit puts in the wrong places.
//
// macOS only (PDFKit, Vision). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/ocr.swift sources/joradp/A2026025.pdf 4 11 ar-SA > ocr.jsonl
import Foundation
import PDFKit
import Vision

let a = CommandLine.arguments
guard a.count >= 5, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("usage: ocr.swift file.pdf first-page last-page fr-FR|ar-SA [dpi]\n".data(using: .utf8)!)
    exit(1)
}
let first = Int(a[2])!, last = min(Int(a[3])!, doc.pageCount), lang = a[4]
let dpi = CGFloat(a.count > 5 ? Double(a[5])! : 300)

func json(_ s: String) -> String {
    let data = try! JSONSerialization.data(withJSONObject: [s], options: [])
    return String(String(data: data, encoding: .utf8)!.dropFirst().dropLast())
}

for number in first...last {
    let page = doc.page(at: number - 1)!
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72
    let w = Int(box.width * scale), h = Int(box.height * scale)
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: ctx)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = [lang]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: ctx.makeImage()!, options: [:]).perform([request])
    for o in request.results ?? [] {
        guard let c = o.topCandidates(1).first else { continue }
        let b = o.boundingBox
        print("{\"page\":\(number),\"x\":\(b.minX),\"y\":\(1 - b.maxY),\"w\":\(b.width),\"h\":\(b.height),\"conf\":\(c.confidence),\"text\":\(json(c.string))}")
    }
}
