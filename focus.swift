#!/usr/bin/swift
import Foundation
import AppKit

func currentFocusApp() -> String {
    return NSWorkspace.shared.frontmostApplication?.localizedName ?? "<none>"
}

var prev_name = currentFocusApp()
print("Monitoring focus... (Press Ctrl+C to stop)")
print("Current focus: \(prev_name)")

let updateTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true, block: { _ in
    let new_name = currentFocusApp()
    if prev_name != new_name {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss.SSS"
        print("\(formatter.string(from: Date())) - Focus shifted to: \(new_name)")
        prev_name = new_name
    }
})

RunLoop.current.run()
