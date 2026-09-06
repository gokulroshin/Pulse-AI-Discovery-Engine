import { OpportunitiesResponse, CorpusStats } from './types';

export const FALLBACK_OPPORTUNITIES: OpportunitiesResponse = {
  "scoring_run_id": "cfa593a7-4170-4c76-a804-e5e530630524",
  "computed_at": "2026-09-04T16:37:57.974318",
  "corpus_size": 1938,
  "total_opportunities": 8,
  "opportunities": [
    {
      "score_id": "9a837dca-353f-432c-863f-6e0cceedb170",
      "rank": 1,
      "node_id": "a242f686-6c8a-4768-97ff-8478944d82df",
      "label": "Styling & Outfit Context Deficit",
      "description": "Users struggle to visualize how an item can be styled with their existing wardrobe or worn for specific real-world occasions.",
      "composite_score": 0.869,
      "frequency_score": 1.0,
      "triangulation_score": 0.75,
      "conversion_relevance_score": 0.94,
      "segment_breadth_score": 0.708,
      "actionability_score": 0.9,
      "extraction_count": 642,
      "confidence_level": "high",
      "top_sources": [
        "reddit",
        "appstore",
        "youtube"
      ],
      "top_segments": [
        "western",
        "unknown",
        "mid"
      ],
      "representative_quotes": [
        "Classic decision fatigue: saved 4 black trousers on Myntra (Levi's and others)",
        "I love this olive green crop jacket from Mast & Harbour on my wishlist, but I have no idea what bottoms or footwear to pair it with from my existing wardrobe",
        "Wishlisted this satin slip skirt from Roadster two months ago",
        "I love this olive green crop jacket from Roadster on my wishlist, but I have no idea what bottoms or footwear to pair it with from my existing wardrobe"
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "4c4c42d5-62dd-4d38-9704-5ad2abb6c90b",
      "rank": 2,
      "node_id": "e6c50547-2d40-457b-b550-350734cace4e",
      "label": "Post-Order & Return Policy Friction",
      "description": "Concerns regarding return window convenience, reverse pickup reliability, or exchange friction if the item does not fit.",
      "composite_score": 0.637,
      "frequency_score": 0.576,
      "triangulation_score": 0.5,
      "conversion_relevance_score": 0.94,
      "segment_breadth_score": 0.289,
      "actionability_score": 0.9,
      "extraction_count": 370,
      "confidence_level": "high",
      "top_sources": [
        "playstore",
        "appstore"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "One of the customer care executives hung up on me while I was explaining the issue to her.",
        "I reported the issue to customer support immediately after delivery.",
        "There appears to be no record of past interactions, as I had to explain the situation every time.",
        "Instead of resolving issues, they simply close tickets without providing a solution.",
        "they do not deliver your order, cancle it by themselves and do not refund the amount"
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "25da2efc-dd1d-42b3-b135-84a2168ec420",
      "rank": 3,
      "node_id": "4d04dd9e-05fd-453e-bf29-bccc56450743",
      "label": "Fit & Sizing Confidence Gap",
      "description": "User hesitation caused by size inconsistency, unclear size charts, conflicting review signals, or inability to predict how clothing fits their specific body type.",
      "composite_score": 0.623,
      "frequency_score": 0.308,
      "triangulation_score": 0.5,
      "conversion_relevance_score": 0.94,
      "segment_breadth_score": 0.637,
      "actionability_score": 0.9,
      "extraction_count": 198,
      "confidence_level": "high",
      "top_sources": [
        "playstore",
        "reddit"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "I have ordered dress of purple colour received blue colour and when tried to return. The dress didn't got returned due to quality check.",
        "I had an issue with size so I asked for exchange and they gave a completely different product in exchange.",
        "I immediately requested a return",
        "the product still shows \u201creturnable till a date,\u201d creating confusion.",
        "Why are Libas kurti sizes so inconsistent across different styles? In straight cut M fits, but in A-line I need L"
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "c62ee4d8-8988-4abb-b52b-2fafd7879b12",
      "rank": 4,
      "node_id": "17bf8b82-2420-450f-9643-efc6bc7b4b3f",
      "label": "Wishlist Decision Deferral & Intent Latency",
      "description": "Users proactively save items as a preliminary step or postpone purchases due to choice paralysis, waiting for sales, or seeking secondary opinions.",
      "composite_score": 0.508,
      "frequency_score": 0.033,
      "triangulation_score": 0.5,
      "conversion_relevance_score": 0.86,
      "segment_breadth_score": 0.516,
      "actionability_score": 0.82,
      "extraction_count": 21,
      "confidence_level": "high",
      "top_sources": [
        "playstore",
        "reddit"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "Saved this Roadster tailored blazer in my wishlist.",
        "Saved this Mast & Harbour tailored blazer in my wishlist.",
        "I had this Biba Anarkali kurta in my wishlist for 3 weeks",
        "I had this W Anarkali kurta in my wishlist for 3 weeks"
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "0775f276-2044-4534-93c6-311a3ed9f4ff",
      "rank": 5,
      "node_id": "487ce4cb-9b8d-4367-9b8f-f26393f07d7c",
      "label": "Post-Confirmation Inventory & Order Cancellations",
      "description": "Distrust created when confirmed orders are abruptly canceled due to inventory synchronization failures during sales.",
      "composite_score": 0.5,
      "frequency_score": 0.12,
      "triangulation_score": 0.5,
      "conversion_relevance_score": 0.84,
      "segment_breadth_score": 0.365,
      "actionability_score": 0.8,
      "extraction_count": 77,
      "confidence_level": "high",
      "top_sources": [
        "playstore",
        "reddit"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "some of the orders got cancelled without any satisfactory reason... expected delivery takes a longer time to deliver.",
        "My order was delayed several times without any proper update, and then it was cancelled without my permission or even informing me beforehand.",
        "Almost every time I place an order, I receive a message saying it will be delivered that day, but it gets cancelled at the last moment due to \"unforeseen reasons.\"",
        "They would take too much time delivering my product (for 15 days) and then when they could not deliver the product they canceled it on their own."
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "8e6b10f9-aeaf-460a-a62c-9d8dbecc5726",
      "rank": 6,
      "node_id": "0e513d10-c96f-4eb3-b588-9f33794187b0",
      "label": "Review Authenticity & Trust Deficit",
      "description": "Distrust in on-platform review credibility, fear of sponsored/fake reviews, and an active search for authentic customer try-on photos.",
      "composite_score": 0.45,
      "frequency_score": 0.22,
      "triangulation_score": 0.25,
      "conversion_relevance_score": 0.84,
      "segment_breadth_score": 0.284,
      "actionability_score": 0.8,
      "extraction_count": 141,
      "confidence_level": "medium",
      "top_sources": [
        "playstore"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "every single day the tracking status updates to \"Delivery Failed\" without anyone actually making an attempt or calling me. Your delivery agents are falsely updating the status to clear their quotas",
        "although the order was shipped, it was stuck at the delivery hub for nearly 10 days without any delivery attempt. The tracking status now shows \"delivery failed\" and the package is being returned to the seller.",
        "they mark them as \u201cdelivery attempted\u201d without even trying to deliver. But I was available the whole time.",
        "Consistently \"order is being delivered in 30 minutes\" was being mentioned by different people of Myntra but no proper response."
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "98bc53ec-11f8-4c86-970b-08eda805dfad",
      "rank": 7,
      "node_id": "49777215-e05c-4a32-9ecf-689cf1080bdf",
      "label": "Bookmarking vs. High-Intent Ambiguity",
      "description": "Wishlist utilized primarily as a passive moodboard or aesthetic archive rather than a short-term purchase funnel.",
      "composite_score": 0.385,
      "frequency_score": 0.118,
      "triangulation_score": 0.25,
      "conversion_relevance_score": 0.72,
      "segment_breadth_score": 0.252,
      "actionability_score": 0.75,
      "extraction_count": 76,
      "confidence_level": "medium",
      "top_sources": [
        "playstore"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "When we skip between the apps and open the window of the app it does not start from where we have left, it refreshes and we have to serach again.",
        "The app focuses more on product recommendations than account settings.",
        "I downloaded the app because they advertised \u20b91,000 cashback and \u20b9500 off on the first order.",
        "The collection is trendy"
      ],
      "status": "auto_generated"
    },
    {
      "score_id": "532fb850-86e9-492c-a9e2-7fc5b72dc0f3",
      "rank": 8,
      "node_id": "8f358299-4047-4f7c-90a6-835faa9728fc",
      "label": "Fulfillment & Delivery Tracking Friction",
      "description": "Friction caused by delayed shipments, inaccurate tracking notices, or uncoordinated doorstep delivery attempts.",
      "composite_score": 0.362,
      "frequency_score": 0.045,
      "triangulation_score": 0.25,
      "conversion_relevance_score": 0.75,
      "segment_breadth_score": 0.202,
      "actionability_score": 0.7,
      "extraction_count": 29,
      "confidence_level": "medium",
      "top_sources": [
        "playstore"
      ],
      "top_segments": [
        "general",
        "unknown",
        "unknown"
      ],
      "representative_quotes": [
        "Prices are almost always higher than other ecommerce sites.",
        "The delivery service is extremely slow compared to other online shopping apps.",
        "When we order any product with you then your delivery times are much longer in comparison to other apps.",
        "prices are relatively low from other apps"
      ],
      "status": "auto_generated"
    }
  ]
};

export const FALLBACK_CORPUS_STATS: CorpusStats = {
  "total_documents": 1938,
  "total_extractions": 1554,
  "platform_distribution": {
    "appstore": 295,
    "ecommerce": 36,
    "playstore": 641,
    "reddit": 825,
    "youtube": 141
  },
  "category_distribution": {
    "accessories": 78,
    "ethnic_wear": 222,
    "footwear": 139,
    "general": 772,
    "western": 727
  },
  "gender_distribution": {
    "men": 60,
    "unisex": 2,
    "unknown": 1641,
    "women": 235
  },
  "brand_tier_distribution": {
    "mid": 531,
    "premium": 331,
    "unknown": 892,
    "value": 184
  },
  "last_ingestion_at": "2026-09-04T16:37:58.482776"
};

export interface FallbackSegmentBreakdownItem {
  node_id: string;
  label: string;
  composite_score: number;
  rank: number;
  segment_distribution: Record<string, number>;
}

export interface FallbackSegmentBreakdownResponse {
  dimension: string;
  total_opportunities: number;
  breakdown: FallbackSegmentBreakdownItem[];
}

export const FALLBACK_SEGMENT_BREAKDOWNS: Record<string, FallbackSegmentBreakdownResponse> = {
  category: {
    dimension: 'category',
    total_opportunities: 8,
    breakdown: [
      {
        node_id: 'a242f686-6c8a-4768-97ff-8478944d82df',
        label: 'Styling & Outfit Context Deficit',
        rank: 1,
        composite_score: 0.869,
        segment_distribution: { ethnic_wear: 0.185, western: 0.533, general: 0.199, footwear: 0.083 },
      },
      {
        node_id: 'e6c50547-2d40-457b-b550-350734cace4e',
        label: 'Post-Order & Return Policy Friction',
        rank: 2,
        composite_score: 0.637,
        segment_distribution: { general: 0.886, western: 0.062, accessories: 0.024, footwear: 0.024, ethnic_wear: 0.003 },
      },
      {
        node_id: '4d04dd9e-05fd-453e-bf29-bccc56450743',
        label: 'Fit & Sizing Confidence Gap',
        rank: 3,
        composite_score: 0.623,
        segment_distribution: { general: 0.571, western: 0.258, footwear: 0.035, accessories: 0.01, ethnic_wear: 0.126 },
      },
      {
        node_id: '17bf8b82-2420-450f-9643-efc6bc7b4b3f',
        label: 'Wishlist Decision Deferral & Intent Latency',
        rank: 4,
        composite_score: 0.508,
        segment_distribution: { general: 0.381, western: 0.19, accessories: 0.048, ethnic_wear: 0.381 },
      },
      {
        node_id: '487ce4cb-9b8d-4367-9b8f-f26393f07d7c',
        label: 'Post-Confirmation Inventory & Order Cancellations',
        rank: 5,
        composite_score: 0.5,
        segment_distribution: { general: 0.779, western: 0.078, footwear: 0.026, accessories: 0.013, ethnic_wear: 0.104 },
      },
      {
        node_id: '0e513d10-c96f-4eb3-b588-9f33794187b0',
        label: 'Review Authenticity & Trust Deficit',
        rank: 6,
        composite_score: 0.45,
        segment_distribution: { general: 0.922, western: 0.043, footwear: 0.007, accessories: 0.021, ethnic_wear: 0.007 },
      },
      {
        node_id: '49777215-e05c-4a32-9ecf-689cf1080bdf',
        label: 'Bookmarking vs. High-Intent Ambiguity',
        rank: 7,
        composite_score: 0.385,
        segment_distribution: { general: 0.895, footwear: 0.013, western: 0.053, accessories: 0.039 },
      },
      {
        node_id: '8f358299-4047-4f7c-90a6-835faa9728fc',
        label: 'Fulfillment & Delivery Tracking Friction',
        rank: 8,
        composite_score: 0.362,
        segment_distribution: { general: 0.897, western: 0.069, footwear: 0.034 },
      },
    ],
  },
  gender: {
    dimension: 'gender',
    total_opportunities: 8,
    breakdown: [
      {
        node_id: 'a242f686-6c8a-4768-97ff-8478944d82df',
        label: 'Styling & Outfit Context Deficit',
        rank: 1,
        composite_score: 0.869,
        segment_distribution: { unknown: 0.712, women: 0.232, men: 0.056 },
      },
      {
        node_id: 'e6c50547-2d40-457b-b550-350734cace4e',
        label: 'Post-Order & Return Policy Friction',
        rank: 2,
        composite_score: 0.637,
        segment_distribution: { unknown: 0.924, women: 0.016, men: 0.059 },
      },
      {
        node_id: '4d04dd9e-05fd-453e-bf29-bccc56450743',
        label: 'Fit & Sizing Confidence Gap',
        rank: 3,
        composite_score: 0.623,
        segment_distribution: { unknown: 0.818, women: 0.101, men: 0.071, unisex: 0.01 },
      },
      {
        node_id: '17bf8b82-2420-450f-9643-efc6bc7b4b3f',
        label: 'Wishlist Decision Deferral & Intent Latency',
        rank: 4,
        composite_score: 0.508,
        segment_distribution: { unknown: 0.952, women: 0.048 },
      },
      {
        node_id: '487ce4cb-9b8d-4367-9b8f-f26393f07d7c',
        label: 'Post-Confirmation Inventory & Order Cancellations',
        rank: 5,
        composite_score: 0.5,
        segment_distribution: { unknown: 0.948, men: 0.052 },
      },
      {
        node_id: '0e513d10-c96f-4eb3-b588-9f33794187b0',
        label: 'Review Authenticity & Trust Deficit',
        rank: 6,
        composite_score: 0.45,
        segment_distribution: { unknown: 0.901, men: 0.064, women: 0.021, unisex: 0.014 },
      },
      {
        node_id: '49777215-e05c-4a32-9ecf-689cf1080bdf',
        label: 'Bookmarking vs. High-Intent Ambiguity',
        rank: 7,
        composite_score: 0.385,
        segment_distribution: { unknown: 0.934, men: 0.066 },
      },
      {
        node_id: '8f358299-4047-4f7c-90a6-835faa9728fc',
        label: 'Fulfillment & Delivery Tracking Friction',
        rank: 8,
        composite_score: 0.362,
        segment_distribution: { unknown: 0.966, men: 0.034 },
      },
    ],
  },
  brand_tier: {
    dimension: 'brand_tier',
    total_opportunities: 8,
    breakdown: [
      {
        node_id: 'a242f686-6c8a-4768-97ff-8478944d82df',
        label: 'Styling & Outfit Context Deficit',
        rank: 1,
        composite_score: 0.869,
        segment_distribution: { value: 0.132, mid: 0.371, premium: 0.251, unknown: 0.246 },
      },
      {
        node_id: 'e6c50547-2d40-457b-b550-350734cace4e',
        label: 'Post-Order & Return Policy Friction',
        rank: 2,
        composite_score: 0.637,
        segment_distribution: { unknown: 0.808, mid: 0.192 },
      },
      {
        node_id: '4d04dd9e-05fd-453e-bf29-bccc56450743',
        label: 'Fit & Sizing Confidence Gap',
        rank: 3,
        composite_score: 0.623,
        segment_distribution: { unknown: 0.566, mid: 0.293, premium: 0.086, value: 0.056 },
      },
      {
        node_id: '17bf8b82-2420-450f-9643-efc6bc7b4b3f',
        label: 'Wishlist Decision Deferral & Intent Latency',
        rank: 4,
        composite_score: 0.508,
        segment_distribution: { unknown: 0.476, mid: 0.381, value: 0.143 },
      },
      {
        node_id: '487ce4cb-9b8d-4367-9b8f-f26393f07d7c',
        label: 'Post-Confirmation Inventory & Order Cancellations',
        rank: 5,
        composite_score: 0.5,
        segment_distribution: { unknown: 0.623, mid: 0.351, value: 0.026 },
      },
      {
        node_id: '0e513d10-c96f-4eb3-b588-9f33794187b0',
        label: 'Review Authenticity & Trust Deficit',
        rank: 6,
        composite_score: 0.45,
        segment_distribution: { unknown: 0.823, mid: 0.177 },
      },
      {
        node_id: '49777215-e05c-4a32-9ecf-689cf1080bdf',
        label: 'Bookmarking vs. High-Intent Ambiguity',
        rank: 7,
        composite_score: 0.385,
        segment_distribution: { unknown: 0.934, mid: 0.066 },
      },
      {
        node_id: '8f358299-4047-4f7c-90a6-835faa9728fc',
        label: 'Fulfillment & Delivery Tracking Friction',
        rank: 8,
        composite_score: 0.362,
        segment_distribution: { unknown: 0.759, mid: 0.241 },
      },
    ],
  },
};

