// Prints each run of text that PDFKit finds on a page, with its position, as one JSON line:
// x, y, w and h are fractions of the page, y from the top, like ocr.swift's output.
// The Arabic edition of JO n° 78 of 2019 stores its text one word at a time, so
// columns.swift can't rebuild its lines; tools/gazette/lists.py does it from these
// positions instead.
//
// macOS only (PDFKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/runs.swift sources/joradp/A2019078.pdf 13 16 > runs.jsonl
import Foundation
import PDFKit

let a = CommandLine.arguments
guard a.count >= 4, let doc = PDFDocument(url: URL(fileURLWithPath: a[1])) else {
    FileHandle.standardError.write("usage: runs.swift file.pdf first-page last-page\n".data(using: .utf8)!)
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
    for run in page.selection(for: box)?.selectionsByLine() ?? [] {
        let text = (run.string ?? "").trimmingCharacters(in: .whitespacesAndNewlines)
        if text.isEmpty { continue }
        let b = run.bounds(for: page)
        let x = (b.minX - box.minX) / box.width, y = (box.maxY - b.maxY) / box.height
        print("{\"page\":\(number),\"x\":\(x),\"y\":\(y),\"w\":\(b.width / box.width),\"h\":\(b.height / box.height),\"text\":\(json(text))}")
    }
}
