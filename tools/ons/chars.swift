// Prints every character that PDFKit finds on a page, with its box, as one JSON line:
// x, y, w and h are fractions of the page, y from the top, like tools/gazette/runs.swift.
// ONS's code géographique stores its Arabic names in pieces, some of them run together with the
// codes, so the names are rebuilt from the characters' places instead (tools/ons/codes.py).
//
// macOS only (PDFKit). Used once, to transcribe the list; the build doesn't need it.
//
//   swift tools/ons/chars.swift sources/ons/code_geo_2021.pdf 4 66 > work/ons/2021.chars.jsonl
import Foundation
import PDFKit

let a = CommandLine.arguments
guard a.count >= 4, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("usage: chars.swift file.pdf first-page last-page\n".data(using: .utf8)!)
    exit(1)
}
let first = Int(a[2])!, last = min(Int(a[3])!, doc.pageCount)

func json(_ s: String) -> String {
    let data = try! JSONSerialization.data(withJSONObject: [s], options: [])
    return String(String(data: data, encoding: .utf8)!.dropFirst().dropLast())
}

for number in first...last {
    let page = doc.page(at: number - 1)!
    let box = page.bounds(for: .mediaBox)
    let text = (page.string ?? "") as NSString
    for i in 0..<text.length {
        guard let one = page.selection(for: NSRange(location: i, length: 1)), let c = one.string,
              !c.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { continue }
        let r = one.bounds(for: page)
        if r.isEmpty || r.isNull { continue }
        let x = (r.minX - box.minX) / box.width, y = (box.maxY - r.maxY) / box.height
        print("{\"page\":\(number),\"i\":\(i),\"x\":\(x),\"y\":\(y),\"w\":\(r.width / box.width),\"h\":\(r.height / box.height),\"c\":\(json(c))}")
    }
}
