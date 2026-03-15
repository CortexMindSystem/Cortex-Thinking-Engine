//
//  APIServiceTests.swift
//  CortexOSKitTests
//
//  Tests for APIService URL construction and error types.
//

import XCTest
@testable import CortexOSKit

final class APIErrorTests: XCTestCase {

    func testInvalidURLDescription() {
        let error = APIError.invalidURL
        XCTAssertEqual(error.errorDescription, "Invalid server URL.")
    }

    func testHTTPErrorDescription() {
        let error = APIError.httpError(statusCode: 404, body: "Not Found")
        XCTAssertEqual(error.errorDescription, "HTTP 404: Not Found")
    }

    func testDecodingErrorDescription() {
        let underlying = NSError(domain: "test", code: 1, userInfo: [NSLocalizedDescriptionKey: "bad json"])
        let error = APIError.decodingError(underlying)
        XCTAssertTrue(error.errorDescription?.contains("Decoding error") ?? false)
    }

    func testNetworkErrorDescription() {
        let underlying = NSError(domain: NSURLErrorDomain, code: -1009, userInfo: [NSLocalizedDescriptionKey: "offline"])
        let error = APIError.networkError(underlying)
        XCTAssertTrue(error.errorDescription?.contains("Network error") ?? false)
    }
}

@MainActor
final class APIServiceInitTests: XCTestCase {

    func testDefaultBaseURL() {
        let service = APIService(baseURL: "http://test:9999")
        XCTAssertEqual(service.baseURL, "http://test:9999")
    }
}

final class PipelineStepsResponseTests: XCTestCase {

    func testDecode() throws {
        let json = """
        {"steps": ["ingest", "score", "focus"]}
        """.data(using: .utf8)!

        let resp = try JSONDecoder().decode(PipelineStepsResponse.self, from: json)
        XCTAssertEqual(resp.steps, ["ingest", "score", "focus"])
    }
}
