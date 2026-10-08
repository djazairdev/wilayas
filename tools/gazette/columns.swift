// Prints the text of each page of a text PDF column by column, so the gazette's two
// columns don't get mixed up. Arabic pages are printed right column first. The Arabic
// comes out in display order; tools/gazette/lists.py turns it back into normal text.
//
// macOS only (PDFKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/columns.swift ar sources/joradp/A2026025.pdf 4 9 > A2026025.txt
import Foundation
import PDFKit

let args = CommandLine.arguments
guard args.count >= 3, let doc = PDFDocument(url: URL(fileURLWithPath: args[2])) else {
    FileHandle.standardError.write("usage: columns.swift ar|fr file.pdf [first-page last-page]\n".data(using: .utf8)!)
    exit(1)
}
let rtl = args[1] == "ar"
let first = args.count > 3 ? Int(args[3])! : 1
let last = args.count > 4 ? min(Int(args[4])!, doc.pageCount) : doc.pageCount
let head = CGFloat(Double(ProcessInfo.processInfo.environment["HEAD_POINTS"] ?? "48")!)

for number in first...last {
    guard let page = doc.page(at: number - 1) else { continue }
    let box = page.bounds(for: .mediaBox)
    // Leave out the running head (title, issue number, dates), which spans both columns.
    let height = box.height - head
    let left = CGRect(x: box.minX, y: box.minY, width: box.width / 2, height: height)
    let right = CGRect(x: box.midX, y: box.minY, width: box.width / 2, height: height)
    for (name, rect) in (rtl ? [("right", right), ("left", left)] : [("left", left), ("right", right)]) {
        print("=== page \(number) \(name) ===")
        print(page.selection(for: rect)?.string ?? "")
    }
}
