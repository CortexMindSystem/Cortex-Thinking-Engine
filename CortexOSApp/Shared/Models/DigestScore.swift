//
//  DigestScore.swift
//  CortexOS
//
//  Digest evaluation metrics from the scoring engine.
//

import Foundation

struct ArticleScoreItem: Codable, Identifiable {
    var id: String { title }
    let title: String
    let score: Double
}

struct DigestScore: Codable {
    let totalArticles: Int
    let aiArticleRatio: Double
    let highSignalRatio: Double
    let signalToNoiseRatio: Double
    let contextKeywordCoverage: Double
    let projectFitScore: Double
    let topArticles: [ArticleScoreItem]

    enum CodingKeys: String, CodingKey {
        case totalArticles = "total_articles"
        case aiArticleRatio = "ai_article_ratio"
        case highSignalRatio = "high_signal_ratio"
        case signalToNoiseRatio = "signal_to_noise_ratio"
        case contextKeywordCoverage = "context_keyword_coverage"
        case projectFitScore = "project_fit_score"
        case topArticles = "top_articles"
    }
}

struct DigestEvalRequest: Codable {
    var path: String?
    var context: [String]?
}
