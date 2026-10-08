// Renders regions of pages as bilevel bitmaps, to measure the shapes of letters on a scan.
// Reads JSON lines on stdin, one region each:
//   {"pdf": "sources/joradp/A1991041.pdf", "page": 30, "x": 0.65, "y": 0.37, "w": 0.12, "h": 0.02, "dpi": 305}
// where x, y, w and h are fractions of the page, y from the top, and prints one JSON line per
// region, {"rows": ["..##..", ...]}, with '#' for each pixel darker than mid-grey.
//
// macOS only (PDFKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   python3 tools/gazette/alifs.py work/F1991041.rows.jsonl work/A1991041.rows.jsonl   (runs it)
import Foundation
import PDFKit

var docs: [String: PDFDocument] = [:]
while let line = readLine() {
    guard let data = line.data(using: .utf8),
          let job = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
          let path = job["pdf"] as? String, let number = job["page"] as? Int
    else {
        FileHandle.standardError.write("bad line: \(line)\n".data(using: .utf8)!)
        exit(1)
    }
    if docs[path] == nil { docs[path] = PDFDocument(url: URL(fileURLWithPath: path)) }
    guard let page = docs[path]?.page(at: number - 1) else {
        FileHandle.standardError.write("no page \(number) in \(path)\n".data(using: .utf8)!)
        exit(1)
    }
    func value(_ key: String) -> CGFloat { CGFloat((job[key] as! NSNumber).doubleValue) }
    let (rx, ry, rw, rh, dpi) = (value("x"), value("y"), value("w"), value("h"), value("dpi"))
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72
    let w = max(1, Int(rw * box.width * scale)), h = max(1, Int(rh * box.height * scale))
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w,
                        space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGImageAlphaInfo.none.rawValue)!
    ctx.setFillColor(gray: 1, alpha: 1)
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    ctx.translateBy(x: -(box.minX + rx * box.width), y: -(box.minY + (1 - ry - rh) * box.height))
    page.draw(with: .mediaBox, to: ctx)
    let pixels = ctx.data!.bindMemory(to: UInt8.self, capacity: w * h)
    var rows: [String] = []
    for r in 0..<h {
        var s = ""
        for x in 0..<w { s += pixels[r * w + x] < 128 ? "#" : "." }
        rows.append(s)
    }
    let out = try! JSONSerialization.data(withJSONObject: ["rows": rows])
    print(String(data: out, encoding: .utf8)!)
}
