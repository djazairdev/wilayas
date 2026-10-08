// Finds the horizontal rules of the tables on rendered pages: the lines that separate the
// rows of the daïra tables in Decrees 91-306 (a scan) and 26-253. Prints one JSON line per
// rule, with its position as a fraction of the page, y from the top, in each half-page column:
//   {"page": 4, "side": "right", "y": 0.2131}
// A rule is a pixel row holding one long stroke: an unbroken run of darkish pixels (gaps of up to
// three allowed, for the scan's breaks) over half the column's width or more. A pixel counts as
// darkish when it or one within two rows of it is, as the scans are slightly skewed. Text, even
// Arabic with its baseline, breaks between words; a faint rule can be lighter than a line of text.
//
// macOS only (PDFKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/rules.swift sources/joradp/F1991041.pdf 3 28 > work/F1991041.rules.jsonl
import Foundation
import PDFKit

let a = CommandLine.arguments
guard a.count >= 4, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("usage: rules.swift file.pdf first-page last-page [dpi]\n".data(using: .utf8)!)
    exit(1)
}
let first = Int(a[2])!, last = min(Int(a[3])!, doc.pageCount)
let dpi = CGFloat(a.count > 4 ? Double(a[4])! : 150)

for number in first...last {
    let page = doc.page(at: number - 1)!
    let box = page.bounds(for: .mediaBox)
    let scale = dpi / 72
    let w = Int(box.width * scale), h = Int(box.height * scale)
    let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w,
                        space: CGColorSpaceCreateDeviceGray(), bitmapInfo: CGImageAlphaInfo.none.rawValue)!
    ctx.setFillColor(gray: 1, alpha: 1)
    ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
    ctx.scaleBy(x: scale, y: scale)
    page.draw(with: .mediaBox, to: ctx)
    let pixels = ctx.data!.bindMemory(to: UInt8.self, capacity: w * h)
    for (side, x0, x1) in [("left", 0, w / 2), ("right", w / 2, w)] {
        var run: [Int] = []
        func flush() {
            if !run.isEmpty {
                // the bitmap's first row is the top of the page
                let y = Double(run.reduce(0, +)) / Double(run.count) / Double(h)
                print("{\"page\":\(number),\"side\":\"\(side)\",\"y\":\(String(format: "%.4f", y))}")
                run = []
            }
        }
        for row in 0..<h {
            var longest = 0, start = -1, gap = 0
            for x in x0..<x1 {
                var dark = false
                for r in max(0, row - 2)...min(h - 1, row + 2) where pixels[r * w + x] < 200 { dark = true; break }
                if dark {
                    if start < 0 { start = x }
                    gap = 0
                    longest = max(longest, x - start + 1)
                } else if start >= 0 {
                    gap += 1
                    if gap > 3 { start = -1; gap = 0 }
                }
            }
            if longest * 2 > (x1 - x0) {
                if let last = run.last, row - last > 1 { flush() }
                run.append(row)
            } else if let last = run.last, row - last > 1 {
                flush()
            }
        }
        flush()
    }
}
