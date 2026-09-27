import asyncio
import time
import unittest

from third_party_apis.axiom_trade_api.request_pacer import (
    AxiomRequestPacer,
    background_axiom_request,
)


class AxiomRequestPacerTests(unittest.IsolatedAsyncioTestCase):
    async def test_prioritizes_new_tokens_and_spaces_http_starts(self) -> None:
        pacer = AxiomRequestPacer(interval_seconds=0.04)
        order: list[tuple[str, float]] = []

        async def wait_for_turn(name: str, background: bool) -> None:
            if background:
                with background_axiom_request():
                    await pacer.wait_turn()
            else:
                await pacer.wait_turn()
            order.append((name, time.monotonic()))
            pacer.release_turn()

        background = asyncio.create_task(wait_for_turn("history", True))
        primary = asyncio.create_task(wait_for_turn("new token", False))
        await asyncio.gather(background, primary)
        self.assertEqual([name for name, _ in order], ["new token", "history"])
        self.assertGreaterEqual(order[1][1] - order[0][1], 0.03)
        await pacer.close()

    async def test_cancelled_waiter_does_not_block_following_request(
        self,
    ) -> None:
        pacer = AxiomRequestPacer(interval_seconds=0.04)
        await pacer.wait_turn()
        pacer.release_turn()
        cancelled = asyncio.create_task(pacer.wait_turn())
        await asyncio.sleep(0)
        pending, oldest_age = pacer.queue_stats()
        self.assertEqual(pending, 1)
        self.assertGreaterEqual(oldest_age, 0)
        cancelled.cancel()
        await asyncio.gather(cancelled, return_exceptions=True)
        self.assertEqual(pacer.queue_stats()[0], 0)
        await asyncio.wait_for(pacer.wait_turn(), 0.2)
        pacer.release_turn()
        await pacer.close()

    async def test_saturated_slots_preserve_priority_and_start_spacing(
        self,
    ) -> None:
        pacer = AxiomRequestPacer(interval_seconds=0.04, max_concurrency=1)
        await pacer.wait_turn()
        starts: list[tuple[str, float]] = []

        async def start(name: str, background: bool) -> None:
            if background:
                with background_axiom_request():
                    await pacer.wait_turn()
            else:
                await pacer.wait_turn()
            try:
                starts.append((name, time.monotonic()))
            finally:
                pacer.release_turn()

        history = asyncio.create_task(start("history", True))
        await asyncio.sleep(0)
        fresh = asyncio.create_task(start("new token", False))
        await asyncio.sleep(0)
        self.assertEqual(pacer.queue_stats()[0], 2)
        pacer.release_turn()
        await asyncio.gather(history, fresh)

        self.assertEqual(
            [name for name, _ in starts], ["new token", "history"]
        )
        self.assertGreaterEqual(starts[1][1] - starts[0][1], 0.03)
        await pacer.close()

    async def test_background_history_progresses_during_sustained_new_tokens(
        self,
    ) -> None:
        pacer = AxiomRequestPacer(interval_seconds=0, max_concurrency=1)
        with background_axiom_request():
            await pacer.wait_turn()
        order: list[str] = []

        async def start(name: str, background: bool = False) -> None:
            if background:
                with background_axiom_request():
                    await pacer.wait_turn()
            else:
                await pacer.wait_turn()
            try:
                order.append(name)
            finally:
                pacer.release_turn()

        history = asyncio.create_task(start("history", background=True))
        fresh = [
            asyncio.create_task(start(f"new-{index}")) for index in range(12)
        ]
        await asyncio.sleep(0)
        pacer.release_turn()
        await asyncio.gather(history, *fresh)

        self.assertEqual(order.index("history"), 10)
        await pacer.close()

    async def test_fifo_and_fairness_ignore_cancelled_requests(self) -> None:
        pacer = AxiomRequestPacer(interval_seconds=0, max_concurrency=1)
        with background_axiom_request():
            await pacer.wait_turn()
        order: list[str] = []

        async def start(name: str, background: bool = False) -> None:
            if background:
                with background_axiom_request():
                    await pacer.wait_turn()
            else:
                await pacer.wait_turn()
            order.append(name)
            pacer.release_turn()

        histories = [
            asyncio.create_task(start(f"history-{index}", background=True))
            for index in range(3)
        ]
        fresh = [
            asyncio.create_task(start(f"new-{index}")) for index in range(13)
        ]
        try:
            await asyncio.sleep(0)
            histories[0].cancel()
            fresh[0].cancel()
            fresh[5].cancel()
            await asyncio.gather(
                histories[0], fresh[0], fresh[5], return_exceptions=True
            )
            self.assertEqual(pacer.queue_stats()[0], 13)
            pacer.release_turn()
            await asyncio.gather(*histories[1:], *fresh[1:5], *fresh[6:])
            expected_fresh = [
                f"new-{index}" for index in range(13) if index not in (0, 5)
            ]
            self.assertEqual(
                order,
                expected_fresh[:10]
                + ["history-1"]
                + expected_fresh[10:]
                + ["history-2"],
            )
        finally:
            await pacer.close()

    async def test_close_cancels_both_queues(self) -> None:
        pacer = AxiomRequestPacer(interval_seconds=0, max_concurrency=1)
        await pacer.wait_turn()
        with background_axiom_request():
            background = asyncio.create_task(pacer.wait_turn())
        foreground = asyncio.create_task(pacer.wait_turn())
        await asyncio.sleep(0)
        self.assertEqual(pacer.queue_stats()[0], 2)
        await pacer.close()
        results = await asyncio.gather(
            foreground, background, return_exceptions=True
        )
        self.assertTrue(
            all(
                isinstance(result, asyncio.CancelledError)
                for result in results
            )
        )
        self.assertEqual(pacer.queue_stats(), (0, 0.0))
        pacer.release_turn()
