from orchestrator.orchestrator import PatristicQuoteOrchestrator


_orchestrator = PatristicQuoteOrchestrator()


async def get_patristic_text(passagem: str, padre: str) -> list:
    return await _orchestrator.get_patristic_text(passagem, padre)
