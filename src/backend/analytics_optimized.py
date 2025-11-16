"""
Analytics Service - Optimized for Performance
Provides aggregated data for dashboard and statistics
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from pymongo import DESCENDING, ASCENDING
from db import get_db

log = logging.getLogger("riceguard.analytics")

class AnalyticsService:
    """Optimized analytics service with efficient database queries"""

    def __init__(self):
        self.db = get_db()

    async def get_user_scan_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get optimized scan summary for a user with aggregation pipeline
        """
        try:
            user_obj_id = {"$toObjectId": user_id}

            # Single aggregation pipeline for all statistics
            pipeline = [
                {"$match": {"userId": user_obj_id}},
                {
                    "$group": {
                        "_id": None,
                        "totalScans": {"$sum": 1},
                        "avgConfidence": {"$avg": "$confidence"},
                        "maxConfidence": {"$max": "$confidence"},
                        "minConfidence": {"$min": "$confidence"},
                        "diseaseBreakdown": {
                            "$push": {
                                "disease": "$label",
                                "confidence": "$confidence",
                                "createdAt": "$createdAt"
                            }
                        },
                        "firstScan": {"$min": "$createdAt"},
                        "lastScan": {"$max": "$createdAt"},
                        "recentScans": {
                            "$push": {
                                "label": "$label",
                                "confidence": "$confidence",
                                "createdAt": "$createdAt",
                                "imageUrl": "$imageUrl"
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "totalScans": 1,
                        "avgConfidence": {"$round": ["$avgConfidence", 2]},
                        "maxConfidence": 1,
                        "minConfidence": 1,
                        "diseaseBreakdown": 1,
                        "firstScan": 1,
                        "lastScan": 1,
                        "recentScans": {"$slice": ["$recentScans", 5]}  # Limit to 5 recent scans
                    }
                }
            ]

            result = await self.db.scans.aggregate_one(pipeline)

            if not result:
                return {
                    "totalScans": 0,
                    "avgConfidence": 0,
                    "maxConfidence": 0,
                    "minConfidence": 0,
                    "diseaseBreakdown": {},
                    "firstScan": None,
                    "lastScan": None,
                    "recentScans": []
                }

            # Process disease breakdown counts
            disease_counts = {}
            for item in result.get("diseaseBreakdown", []):
                disease = item.get("disease")
                if disease:
                    disease_counts[disease] = disease_counts.get(disease, 0) + 1

            # Calculate days since last scan
            last_scan = result.get("lastScan")
            days_since_last = None
            if last_scan:
                days_since_last = (datetime.now(timezone.utc) - last_scan).days

            return {
                **result,
                "diseaseBreakdown": disease_counts,
                "daysSinceLastScan": days_since_last,
                "uniqueDiseases": len(disease_counts)
            }

        except Exception as e:
            log.error(f"Error getting user scan summary: {e}")
            return {}

    async def get_disease_trends(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get disease trends over time using efficient aggregation
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            user_obj_id = {"$toObjectId": user_id}

            pipeline = [
                {
                    "$match": {
                        "userId": user_obj_id,
                        "createdAt": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "disease": "$label",
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$createdAt"
                                }
                            }
                        },
                        "count": {"$sum": 1},
                        "avgConfidence": {"$avg": "$confidence"},
                        "scans": {
                            "$push": {
                                "confidence": "$confidence",
                                "createdAt": "$createdAt"
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.disease",
                        "dailyData": {
                            "$push": {
                                "date": "$_id.date",
                                "count": "$count",
                                "avgConfidence": {"$round": ["$avgConfidence", 2]}
                            }
                        },
                        "totalCount": {"$sum": "$count"},
                        "overallAvgConfidence": {"$avg": "$avgConfidence"},
                        "dates": {"$addToSet": "$_id.date"}
                    }
                },
                {
                    "$sort": {"totalCount": -1}
                }
            ]

            results = await self.db.scans.aggregate(pipeline).to_list(length=None)

            return {
                "trends": results,
                "period": f"Last {days} days",
                "totalDiseases": len(results)
            }

        except Exception as e:
            log.error(f"Error getting disease trends: {e}")
            return {"trends": [], "period": f"Last {days} days", "totalDiseases": 0}

    async def get_heatmap_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Get optimized heatmap data for disease visualization
        """
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=days)
            user_obj_id = {"$toObjectId": user_id}

            # Efficient aggregation for heatmap data
            pipeline = [
                {
                    "$match": {
                        "userId": user_obj_id,
                        "createdAt": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "disease": "$label",
                            "timePeriod": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$createdAt"
                                }
                            }
                        },
                        "count": {"$sum": 1},
                        "avgConfidence": {"$avg": "$confidence"},
                        "scans": {
                            "$push": {
                                "confidence": "$confidence",
                                "createdAt": "$createdAt"
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.disease",
                        "timePeriods": {
                            "$push": {
                                "period": "$_id.timePeriod",
                                "count": "$count",
                                "avgConfidence": {"$round": ["$avgConfidence", 2]}
                            }
                        },
                        "totalCount": {"$sum": "$count"},
                        "overallAvgConfidence": {"$avg": "$avgConfidence"}
                    }
                },
                {
                    "$sort": {"totalCount": -1}
                }
            ]

            results = await self.db.scans.aggregate(pipeline).to_list(length=None)

            # Calculate total scans for percentage calculation
            total_scans = sum(result["totalCount"] for result in results)

            return {
                "heatmapData": results,
                "totalScans": total_scans,
                "period": f"Last {days} days",
                "diseaseCount": len(results)
            }

        except Exception as e:
            log.error(f"Error getting heatmap data: {e}")
            return {"heatmapData": [], "totalScans": 0, "period": f"Last {days} days", "diseaseCount": 0}

    async def get_scan_streak_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's scanning streak information efficiently
        """
        try:
            user_obj_id = {"$toObjectId": user_id}

            pipeline = [
                {"$match": {"userId": user_obj_id}},
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$createdAt"
                            }
                        },
                        "scanCount": {"$sum": 1},
                        "firstScan": {"$min": "$createdAt"},
                        "lastScan": {"$max": "$createdAt"}
                    }
                },
                {
                    "$sort": {"_id": -1}  // Sort by date descending
                }
            ]

            daily_scans = await self.db.scans.aggregate(pipeline).to_list(length=None)

            if not daily_scans:
                return {
                    "currentStreak": 0,
                    "longestStreak": 0,
                    "totalActiveDays": 0,
                    "mostRecentScan": None
                }

            # Calculate current streak
            current_streak = 0
            longest_streak = 0
            temp_streak = 0

            today = datetime.now(timezone.utc).date()

            for i, day_data in enumerate(daily_scans):
                scan_date = datetime.fromisoformat(day_data["_id"]).date()

                # Calculate streaks
                if i == 0:
                    # Check if most recent day is today or yesterday
                    days_diff = (today - scan_date).days
                    if days_diff <= 1:
                        current_streak = 1
                    temp_streak = 1
                else:
                    prev_date = datetime.fromisoformat(daily_scans[i-1]["_id"]).date()
                    if (prev_date - scan_date).days == 1:
                        temp_streak += 1
                        if i == 0 or current_streak > 0:
                            current_streak += 1
                    else:
                        longest_streak = max(longest_streak, temp_streak)
                        temp_streak = 1
                        if current_streak > 0 and i > 0:
                            break  # Break current streak calculation

            longest_streak = max(longest_streak, temp_streak)

            return {
                "currentStreak": current_streak,
                "longestStreak": longest_streak,
                "totalActiveDays": len(daily_scans),
                "mostRecentScan": daily_scans[0]["lastScan"] if daily_scans else None
            }

        except Exception as e:
            log.error(f"Error getting scan streak info: {e}")
            return {
                "currentStreak": 0,
                "longestStreak": 0,
                "totalActiveDays": 0,
                "mostRecentScan": None
            }

    async def get_confidence_distribution(self, user_id: str) -> Dict[str, Any]:
        """
        Get confidence score distribution using efficient aggregation
        """
        try:
            user_obj_id = {"$toObjectId": user_id}

            pipeline = [
                {"$match": {"userId": user_obj_id}},
                {
                    "$bucket": {
                        "groupBy": "$confidence",
                        "boundaries": [0, 0.5, 0.7, 0.8, 0.9, 1.0],
                        "default": "other",
                        "output": {
                            "count": {"$sum": 1},
                            "avgConfidence": {"$avg": "$confidence"}
                        }
                    }
                }
            ]

            results = await self.db.scans.aggregate(pipeline).to_list(length=None)

            # Format results for easier consumption
            distribution = {
                "very_low": {"count": 0, "range": "0-50%", "avgConfidence": 0},
                "low": {"count": 0, "range": "50-70%", "avgConfidence": 0},
                "medium": {"count": 0, "range": "70-80%", "avgConfidence": 0},
                "high": {"count": 0, "range": "80-90%", "avgConfidence": 0},
                "very_high": {"count": 0, "range": "90-100%", "avgConfidence": 0}
            }

            for result in results:
                bound = result.get("_id", 0)
                count = result.get("count", 0)
                avg_conf = result.get("avgConfidence", 0)

                if bound == 0:
                    distribution["very_low"] = {"count": count, "range": "0-50%", "avgConfidence": avg_conf}
                elif bound == 0.5:
                    distribution["low"] = {"count": count, "range": "50-70%", "avgConfidence": avg_conf}
                elif bound == 0.7:
                    distribution["medium"] = {"count": count, "range": "70-80%", "avgConfidence": avg_conf}
                elif bound == 0.8:
                    distribution["high"] = {"count": count, "range": "80-90%", "avgConfidence": avg_conf}
                elif bound == 0.9:
                    distribution["very_high"] = {"count": count, "range": "90-100%", "avgConfidence": avg_conf}

            total_scans = sum(bucket["count"] for bucket in distribution.values())

            return {
                "distribution": distribution,
                "totalScans": total_scans,
                "avgConfidence": sum(
                    bucket["count"] * bucket["avgConfidence"]
                    for bucket in distribution.values()
                ) / total_scans if total_scans > 0 else 0
            }

        except Exception as e:
            log.error(f"Error getting confidence distribution: {e}")
            return {"distribution": {}, "totalScans": 0, "avgConfidence": 0}

# Singleton instance for performance
analytics_service = AnalyticsService()