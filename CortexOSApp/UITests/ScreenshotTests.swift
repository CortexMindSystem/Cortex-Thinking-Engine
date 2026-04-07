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

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launchArguments += ["-UITests", "-Screenshots"]
        app.launch()
        // Give the app time to fully render
        sleep(2)
    }

    // MARK: - iOS Screenshots

    #if os(iOS)
    func testCaptureFocusTab() throws {
        // Focus tab is the default landing screen
        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "01_focus"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func testCaptureDecideTab() throws {
        // Tap the Decide tab
        let decideTab = app.tabBars.buttons["Decide"]
        XCTAssertTrue(decideTab.waitForExistence(timeout: 5))
        decideTab.tap()
        sleep(1)

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "02_decide"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func testCaptureCaptureTab() throws {
        // Tap the Capture tab
        let captureTab = app.tabBars.buttons["Capture"]
        XCTAssertTrue(captureTab.waitForExistence(timeout: 5))
        captureTab.tap()
        sleep(1)

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "03_capture"
        attachment.lifetime = .keepAlways
        add(attachment)
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

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "04_settings"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
    #endif

    // MARK: - macOS Screenshots

    #if os(macOS)
    func testCaptureFocusSidebar() throws {
        // Focus is the default selection
        sleep(1)
        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "01_focus"
        attachment.lifetime = .keepAlways
        add(attachment)
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

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "02_insights"
        attachment.lifetime = .keepAlways
        add(attachment)
    }

    func testCaptureIngestSidebar() throws {
        let sidebar = app.outlines.firstMatch
        if sidebar.waitForExistence(timeout: 5) {
            let cell = sidebar.cells.containing(
                NSPredicate(format: "label CONTAINS[c] 'Ingest'")
            ).firstMatch
            if cell.waitForExistence(timeout: 3) {
                cell.click()
            }
        }
        sleep(1)

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "03_ingest"
        attachment.lifetime = .keepAlways
        add(attachment)
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

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "04_memory"
        attachment.lifetime = .keepAlways
        add(attachment)
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

        let screenshot = app.screenshot()
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = "05_decisions"
        attachment.lifetime = .keepAlways
        add(attachment)
    }
    #endif
}
