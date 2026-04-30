//
//  ScreenshotTests.swift
//  CortexOS
//
//  Automated App Store screenshot capture.
//  Navigates through every key screen and saves a screenshot.
//

import XCTest

final class ScreenshotTests: XCTestCase {
    let app = XCUIApplication()
    private lazy var outputDirectory: URL = {
        let override = ProcessInfo.processInfo.environment["SCREENSHOT_OUTPUT_DIR"]
        let root = override?.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty == false
            ? URL(fileURLWithPath: override!, isDirectory: true)
            : URL(fileURLWithPath: "/Users/pierre/Code/CortexOSLLM/CortexOSApp/screenshot_results", isDirectory: true)
#if os(macOS)
        return root.appendingPathComponent("mac_raw", isDirectory: true)
#elseif os(iOS)
        return root.appendingPathComponent("iphone_raw", isDirectory: true)
#else
        return root
#endif
    }()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launchArguments += ["-UITests", "-Screenshots"]
        app.launch()
        // Give the app time to fully render
        sleep(2)
        try FileManager.default.createDirectory(at: outputDirectory, withIntermediateDirectories: true)
    }

    @discardableResult
    private func captureWindow(_ name: String) -> XCUIScreenshot {
        let screenshot: XCUIScreenshot
#if os(macOS)
        screenshot = app.windows.firstMatch.screenshot()
#else
        screenshot = app.screenshot()
#endif

        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)

        let path = outputDirectory.appendingPathComponent("\(name).png")
        do {
            try screenshot.pngRepresentation.write(to: path)
        } catch {
            XCTFail("Failed to write screenshot \(name): \(error)")
        }
        return screenshot
    }

    // MARK: - iOS Screenshots

    #if os(iOS)
    func testCaptureFocusTab() throws {
        // Focus tab is the default landing screen
        captureWindow("01_focus")
    }

    func testCaptureDecideTab() throws {
        // Tap the Decide tab
        let decideTab = app.tabBars.buttons["Decide"]
        XCTAssertTrue(decideTab.waitForExistence(timeout: 5))
        decideTab.tap()
        sleep(1)

        captureWindow("02_decide")
    }

    func testCaptureCaptureTab() throws {
        // Tap the Capture tab
        let captureTab = app.tabBars.buttons["Capture"]
        XCTAssertTrue(captureTab.waitForExistence(timeout: 5))
        captureTab.tap()
        sleep(1)

        captureWindow("03_capture")
    }

    func testCaptureSettings() throws {
        // Tap the gear icon to open Settings
        let settingsButton = app.navigationBars.buttons.matching(
            NSPredicate(format: "label CONTAINS[c] 'gear' OR label CONTAINS[c] 'settings' OR identifier CONTAINS[c] 'gear'")
        ).firstMatch

        if settingsButton.waitForExistence(timeout: 5) {
            settingsButton.tap()
        } else {
            // Try toolbar buttons
            let toolbarButtons = app.buttons
            for i in 0..<toolbarButtons.count {
                let btn = toolbarButtons.element(boundBy: i)
                if btn.label.lowercased().contains("gear") || btn.label.lowercased().contains("setting") {
                    btn.tap()
                    break
                }
            }
        }
        sleep(1)

        captureWindow("04_settings")
    }
    #endif

    // MARK: - macOS Screenshots

    #if os(macOS)
    func testCaptureFocusSidebar() throws {
        // Focus is the default selection
        sleep(1)
        captureWindow("01_focus")
    }

    func testCaptureInsightsSidebar() throws {
        let sidebar = app.outlines.firstMatch
        if sidebar.waitForExistence(timeout: 5) {
            let insightsCell = sidebar.cells.containing(
                NSPredicate(format: "label CONTAINS[c] 'Insights'")
            ).firstMatch
            if insightsCell.waitForExistence(timeout: 3) {
                insightsCell.click()
            }
        }
        sleep(1)

        captureWindow("02_insights")
    }

    func testCaptureReviewQueueSidebar() throws {
        let sidebar = app.outlines.firstMatch
        if sidebar.waitForExistence(timeout: 5) {
            let cell = sidebar.cells.containing(
                NSPredicate(format: "label CONTAINS[c] 'Review Queue'")
            ).firstMatch
            if cell.waitForExistence(timeout: 3) {
                cell.click()
            }
        }
        sleep(1)

        captureWindow("03_queues")
    }

    func testCaptureMemorySidebar() throws {
        let sidebar = app.outlines.firstMatch
        if sidebar.waitForExistence(timeout: 5) {
            let cell = sidebar.cells.containing(
                NSPredicate(format: "label CONTAINS[c] 'Memory'")
            ).firstMatch
            if cell.waitForExistence(timeout: 3) {
                cell.click()
            }
        }
        sleep(1)

        captureWindow("04_memory")
    }

    func testCaptureDecisionsSidebar() throws {
        let sidebar = app.outlines.firstMatch
        if sidebar.waitForExistence(timeout: 5) {
            let cell = sidebar.cells.containing(
                NSPredicate(format: "label CONTAINS[c] 'Decisions'")
            ).firstMatch
            if cell.waitForExistence(timeout: 3) {
                cell.click()
            }
        }
        sleep(1)

        captureWindow("05_decisions")
    }

    func testCaptureSettingsSidebar() throws {
        let sidebar = app.outlines.firstMatch
        if sidebar.waitForExistence(timeout: 5) {
            let cell = sidebar.cells.containing(
                NSPredicate(format: "label CONTAINS[c] 'Settings'")
            ).firstMatch
            if cell.waitForExistence(timeout: 3) {
                cell.click()
            }
        }
        sleep(1)
        captureWindow("06_settings")
    }

    func testSettingsSyncButtonKeepsAppResponsive() throws {
        let sidebar = app.outlines.firstMatch
        XCTAssertTrue(sidebar.waitForExistence(timeout: 5))

        let settingsCell = sidebar.cells.containing(
            NSPredicate(format: "label CONTAINS[c] 'Settings'")
        ).firstMatch
        XCTAssertTrue(settingsCell.waitForExistence(timeout: 5))
        settingsCell.click()

        let syncButton = app.buttons.containing(
            NSPredicate(format: "label CONTAINS[c] 'Sync'")
        ).firstMatch
        XCTAssertTrue(syncButton.waitForExistence(timeout: 5))
        syncButton.click()

        let focusCell = sidebar.cells.containing(
            NSPredicate(format: "label CONTAINS[c] 'Focus'")
        ).firstMatch
        XCTAssertTrue(focusCell.waitForExistence(timeout: 5))
        focusCell.click()

        let focusContent = app.staticTexts.containing(
            NSPredicate(format: "label CONTAINS[c] 'priority' OR label CONTAINS[c] 'Focus'")
        ).firstMatch
        XCTAssertTrue(focusContent.waitForExistence(timeout: 5))
    }
    #endif
}
