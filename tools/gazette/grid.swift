// Lays PNG crops out in a grid, each under its label, to read many names at a glance.
//
// macOS only (AppKit). Used once, to transcribe the gazette; the build doesn't need it.
//
//   swift tools/gazette/grid.swift sheet.png 3 1=crop-1.png 2=crop-2.png ...
import AppKit

let a = CommandLine.arguments
guard a.count >= 4, let columns = Int(a[2]), columns > 0 else {
    FileHandle.standardError.write("usage: grid.swift out.png columns label=crop.png ...\n".data(using: .utf8)!)
    exit(1)
}
let out = a[1]
let items = a.dropFirst(3).map { s -> (String, NSBitmapImageRep) in
    let p = s.split(separator: "=", maxSplits: 1)
    return (String(p[0]), NSImage(contentsOfFile: String(p[1]))!.representations.first as! NSBitmapImageRep)
}
let label = 30, gap = 14
let cellW = items.map { $0.1.pixelsWide }.max()! + gap
let rows = (items.count + columns - 1) / columns
var rowH: [Int] = []
for r in 0..<rows {
    rowH.append(items[(r * columns)..<min((r + 1) * columns, items.count)].map { $0.1.pixelsHigh }.max()! + label + gap)
}
let width = cellW * columns, height = rowH.reduce(0, +)
let img = NSImage(size: NSSize(width: width, height: height))
img.lockFocus()
NSColor.white.setFill(); NSRect(x: 0, y: 0, width: width, height: height).fill()
var top = height
for r in 0..<rows {
    for c in 0..<columns where r * columns + c < items.count {
        let (name, rep) = items[r * columns + c]
        let x = c * cellW
        (name as NSString).draw(at: NSPoint(x: x + 4, y: top - label + 4),
                                withAttributes: [.font: NSFont.boldSystemFont(ofSize: 20), .foregroundColor: NSColor.systemRed])
        rep.draw(in: NSRect(x: x, y: top - label - rep.pixelsHigh, width: rep.pixelsWide, height: rep.pixelsHigh))
        NSColor.lightGray.setFill(); NSRect(x: x + cellW - gap / 2, y: top - rowH[r], width: 1, height: rowH[r]).fill()
    }
    top -= rowH[r]
    NSColor.lightGray.setFill(); NSRect(x: 0, y: top + gap / 2, width: width, height: 1).fill()
}
img.unlockFocus()
let bmp = NSBitmapImageRep(cgImage: img.cgImage(forProposedRect: nil, context: nil, hints: nil)!)
try! bmp.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: out))
