from src.field_service_digest import DigestRequest, build_weekly_digest


def test_digest_selects_only_active_orders_needing_follow_up() -> None:
    request = DigestRequest.model_validate(
        {
            "audience": "North region dispatch",
            "week_ending": "2026-09-25",
            "work_orders": [
                {
                    "work_order_id": "WO-104",
                    "customer_name": "Aster Pharmacy",
                    "technician_name": "Mina",
                    "dispatch_status": "in_progress",
                    "photo_urls": [],
                },
                {
                    "work_order_id": "WO-105",
                    "customer_name": "Harbor Dental",
                    "technician_name": "Luis",
                    "dispatch_status": "dispatched",
                    "photo_urls": ["https://media.example/wo-105-arrival.jpg"],
                    "technician_follow_up": True,
                },
                {
                    "work_order_id": "WO-106",
                    "customer_name": "Cedar Market",
                    "technician_name": "Mina",
                    "dispatch_status": "completed",
                    "photo_urls": [],
                },
            ],
        }
    )

    digest = build_weekly_digest(request)

    assert digest.total_work_orders == 3
    assert digest.photo_count == 1
    assert digest.dispatch_counts == {"in_progress": 1, "dispatched": 1, "completed": 1}
    assert [(item.work_order_id, item.reason) for item in digest.follow_ups] == [
        ("WO-104", "missing_photos"),
        ("WO-105", "technician_flagged"),
    ]
