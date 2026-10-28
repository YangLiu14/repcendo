import XCTest

final class RepcendoUITests: XCTestCase {
    func testOfflineAnimationsAndWorkoutEntry() {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        func expectPlayback(_ playing: Bool, identifier: String = "animationPlayPause") {
            let button = app.buttons[identifier]
            XCTAssertTrue(button.exists, app.debugDescription)
            let expectation = XCTNSPredicateExpectation(
                predicate: NSPredicate(format: "label CONTAINS %@", playing ? "暂停" : "播放"), object: button)
            XCTAssertEqual(XCTWaiter.wait(for: [expectation], timeout: 10), .completed)
        }
        for id in ["0043", "0025", "0861"] {
            app.launch()
            app.buttons["动作库"].firstMatch.tap()
            let search = app.searchFields.firstMatch
            XCTAssertTrue(search.waitForExistence(timeout: 5))
            search.tap(); search.typeText(id)
            app.buttons["exercise-\(id)"].tap()
            XCTAssertTrue(app.buttons["animationPlayPause"].waitForExistence(timeout: 5))
            for sex in ["男性", "女性"] {
                app.segmentedControls["animationCharacter"].buttons[sex].tap()
                expectPlayback(true)
                screenshot("animation-\(id)-\(sex)")
                app.buttons["animationPlayPause"].tap()
                expectPlayback(false)
                app.buttons["animationReplay"].tap()
                expectPlayback(true)
            }
            if id == "0043" {
                app.buttons["animationPlayPause"].tap()
                expectPlayback(false)
                app.buttons["animationFullScreen"].tap()
                XCTAssertTrue(app.buttons["animationExitFullScreen"].waitForExistence(timeout: 5))
                expectPlayback(true, identifier: "fullScreenPlayPause")
                Thread.sleep(forTimeInterval: 6) // Exercise a complete five-second loop.
                expectPlayback(true, identifier: "fullScreenPlayPause")
                screenshot("animation-fullscreen")
                app.buttons["animationExitFullScreen"].tap()
                expectPlayback(true)
                app.buttons["animationFullScreen"].tap()
                expectPlayback(true, identifier: "fullScreenPlayPause")
                XCUIDevice.shared.press(.home)
                app.activate()
                expectPlayback(false, identifier: "fullScreenPlayPause")
                app.buttons["animationExitFullScreen"].tap()
                expectPlayback(false)
                app.buttons["animationPlayPause"].tap()
                expectPlayback(true)
            }
            XCUIDevice.shared.press(.home)
            app.activate()
            expectPlayback(false)
            app.navigationBars.buttons.element(boundBy: 0).tap()
            app.buttons["exercise-\(id)"].tap()
            expectPlayback(true)
            app.terminate()
        }
        app.launch()
        XCTAssertTrue(app.buttons["previewExample"].waitForExistence(timeout: 5), "Use a dedicated fresh QA simulator.")
        app.buttons["previewExample"].tap()
        app.buttons["confirmImport"].tap()
        app.buttons["startWorkout"].tap()
        let weight = app.textFields["weight-0"].firstMatch
        reveal(weight, in: app)
        weight.tap(); weight.typeText("20")
        app.buttons["收起键盘"].tap()
        let demo = app.buttons["workout-demo-0025"]
        if !demo.isHittable { app.swipeDown() }
        demo.tap()
        XCTAssertTrue(app.buttons["animationPlayPause"].waitForExistence(timeout: 5))
        expectPlayback(true)
        app.navigationBars.buttons.element(boundBy: 0).tap()
        XCTAssertEqual(weight.value as? String, "20.0")
    }

    func testLibraryCategoriesAndSearch() {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        app.launch()
        app.buttons["动作库"].firstMatch.tap()
        let chest = app.buttons["category-chest"]
        XCTAssertTrue(chest.waitForExistence(timeout: 5))
        screenshot("library-categories")
        chest.tap()
        XCTAssertTrue(app.navigationBars["胸部"].waitForExistence(timeout: 5))
        app.buttons["targetFilter"].tap()
        app.buttons["前锯肌"].tap()
        XCTAssertTrue(app.staticTexts["胸部 · 5 个动作"].waitForExistence(timeout: 5))
        screenshot("library-muscle-filter")
        app.navigationBars.buttons.element(boundBy: 0).tap()
        XCTAssertTrue(chest.waitForExistence(timeout: 5))
        if !app.searchFields.firstMatch.exists, app.buttons["搜索"].firstMatch.waitForExistence(timeout: 3) {
            app.buttons["搜索"].firstMatch.tap()
        }
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 5))
        search.tap(); search.typeText("0025")
        let bench = app.buttons["exercise-0025"]
        XCTAssertTrue(bench.waitForExistence(timeout: 5))
        bench.tap()
        reveal(app.staticTexts["主要目标肌肉"], in: app)
        XCTAssertTrue(app.staticTexts["主要目标肌肉"].waitForExistence(timeout: 5))
        screenshot("library-exercise-detail")
        app.terminate()
        app.launchArguments += ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"]
        app.launch()
        app.buttons["动作库"].firstMatch.tap()
        XCTAssertTrue(app.buttons["category-chest"].waitForExistence(timeout: 5))
        reveal(app.buttons["category-chest"], in: app)
        XCTAssertTrue(app.buttons["category-chest"].isHittable)
        screenshot("library-large-text")
    }

    func testTabNavigation() {
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        app.launch()
        XCTAssertTrue(app.buttons["动作库"].firstMatch.waitForExistence(timeout: 10))
        app.buttons["动作库"].firstMatch.tap()
        XCTAssertTrue(app.navigationBars["动作库"].waitForExistence(timeout: 5))
        app.buttons["记录"].firstMatch.tap()
        XCTAssertTrue(app.staticTexts["把进步，留有记录。"].waitForExistence(timeout: 5))
    }

    private func screenshot(_ name: String) {
        let attachment = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }

    private func reveal(_ element: XCUIElement, in app: XCUIApplication) {
        for _ in 0..<6 {
            if element.exists && element.isHittable { return }
            app.swipeUp()
        }
    }

    func testImportLogResumeFinishAndBrowse() throws {
        continueAfterFailure = false
        let app = XCUIApplication()
        app.launchArguments = ["-AppleLanguages", "(zh-Hans)", "-AppleLocale", "zh_CN"]
        app.launch()
        XCTAssertTrue(app.buttons["previewExample"].waitForExistence(timeout: 15), "Run on a fresh QA simulator, never reset a user's data.")
        screenshot("01-welcome")
        app.buttons["previewExample"].tap()
        XCTAssertTrue(app.buttons["confirmImport"].waitForExistence(timeout: 5))
        app.buttons["confirmImport"].tap()
        XCTAssertTrue(app.buttons["startWorkout"].waitForExistence(timeout: 5))
        screenshot("02-plan")
        app.buttons["startWorkout"].tap()
        let weight = app.textFields["weight-0"].firstMatch
        reveal(weight, in: app)
        XCTAssertTrue(weight.waitForExistence(timeout: 5))
        app.buttons["completeSet-0"].firstMatch.tap()
        XCTAssertTrue(app.alerts["操作未完成"].waitForExistence(timeout: 3))
        app.alerts.buttons["知道了"].tap()
        weight.tap(); weight.typeText("20")
        let reps = app.textFields["reps-0"].firstMatch
        reps.tap(); reps.typeText("10")
        app.buttons["收起键盘"].tap()
        app.buttons["completeSet-0"].firstMatch.tap()
        XCTAssertTrue(app.buttons["取消完成第 1 组"].firstMatch.exists)
        screenshot("03-workout")
        app.buttons["稍后继续"].tap()
        app.terminate(); app.launch()
        XCTAssertTrue(app.buttons["继续训练"].waitForExistence(timeout: 5))
        app.buttons["继续训练"].tap()
        XCTAssertTrue(app.buttons["取消完成第 1 组"].firstMatch.waitForExistence(timeout: 5))
        app.buttons["finishWorkout"].tap()
        app.alerts.buttons["保存并结束"].tap()
        let historyReady = XCTNSPredicateExpectation(predicate: NSPredicate(format: "hittable == true"), object: app.buttons["记录"].firstMatch)
        XCTAssertEqual(XCTWaiter.wait(for: [historyReady], timeout: 8), .completed)
        app.buttons["记录"].firstMatch.tap()
        XCTAssertTrue(app.staticTexts["训练历史"].waitForExistence(timeout: 5))
        screenshot("04-history")
        app.swipeUp()
        XCTAssertTrue(app.buttons["导出给 Codex"].exists)
        app.buttons["导出给 Codex"].tap()
        XCTAssertTrue(app.buttons["保存"].waitForExistence(timeout: 8))
        screenshot("05-export")
        app.buttons["保存"].tap()
        let libraryReady = XCTNSPredicateExpectation(predicate: NSPredicate(format: "hittable == true"), object: app.buttons["动作库"].firstMatch)
        XCTAssertEqual(XCTWaiter.wait(for: [libraryReady], timeout: 8), .completed)
        app.buttons["动作库"].firstMatch.tap()
        if !app.searchFields.firstMatch.exists, app.buttons["搜索"].firstMatch.waitForExistence(timeout: 3) {
            app.buttons["搜索"].firstMatch.tap()
        }
        let search = app.searchFields.firstMatch
        XCTAssertTrue(search.waitForExistence(timeout: 5))
        search.tap(); search.typeText("0025")
        XCTAssertTrue(app.buttons["exercise-0025"].waitForExistence(timeout: 5))
        app.buttons["exercise-0025"].tap()
        reveal(app.staticTexts["动作说明"], in: app)
        XCTAssertTrue(app.staticTexts["动作说明"].waitForExistence(timeout: 5))
        screenshot("06-exercise")
        app.terminate()
        app.launchArguments += ["-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"]
        app.launch()
        screenshot("07-large-text")
        reveal(app.buttons["startWorkout"], in: app)
        app.buttons["startWorkout"].tap()
        reveal(app.textFields["weight-0"].firstMatch, in: app)
        screenshot("08-large-text-workout")
        XCUIDevice.shared.orientation = .landscapeLeft
        screenshot("09-landscape")
        XCUIDevice.shared.orientation = .portrait
    }
}
