"""
Unit tests for individual agent implementations.

Tests each agent's run() function in isolation with mocked dependencies.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_research_agent_autonomous_query_generation():
    """Test that research agent generates its own queries autonomously."""
    from app.agents import research
    
    # Mock LLM responses
    with patch("app.agents.research.call_llm") as mock_llm:
        # Mock query generation response
        mock_llm.side_effect = [
            json.dumps({
                "queries": ["AI fitness competitors", "fitness app pricing"],
                "reasoning": "Focus on competitive landscape"
            }),
            json.dumps({
                "is_sufficient": True,
                "confidence_score": 8,
                "gaps": [],
                "recommendation": "stop"
            }),
            "# Research Report\n\nCompetitor analysis shows..."
        ]
        
        # Mock web search
        with patch("app.agents.research._perform_deep_research") as mock_search:
            mock_search.return_value = {
                "results": [{
                    "url": "https://example.com",
                    "title": "Fitness App Market",
                    "content": "Market analysis data...",
                    "raw_content": "Detailed market data..."
                }]
            }
            
            payload = {
                "company_description": "ACME Corp",
                "product_details": "AI fitness app",
                "target_audience": "professionals",
                "goals": "GTM strategy"
            }
            
            result = await research.run("test-job-1", payload)
            
            # Assertions
            assert result["status"] == "completed"
            assert "research_report" in result
            assert result["iterations"] >= 1
            assert "confidence_score" in result
            assert "autonomous_decisions" in result
            assert result["autonomous_decisions"]["query_generation"] == "self-directed"


@pytest.mark.asyncio
async def test_research_agent_iterative_refinement():
    """Test that research agent refines queries when data is insufficient."""
    from app.agents import research
    
    with patch("app.agents.research.call_llm") as mock_llm:
        # First iteration: insufficient data
        # Second iteration: sufficient data
        mock_llm.side_effect = [
            json.dumps({
                "queries": ["query1", "query2"],
                "reasoning": "Initial queries"
            }),
            json.dumps({
                "is_sufficient": False,
                "confidence_score": 4,
                "gaps": ["pricing data missing"],
                "recommendation": "continue",
                "next_queries": ["pricing query"]
            }),
            json.dumps({
                "is_sufficient": True,
                "confidence_score": 8,
                "gaps": [],
                "recommendation": "stop"
            }),
            "# Research Report\n\nFinal report..."
        ]
        
        with patch("app.agents.research._perform_deep_research") as mock_search:
            mock_search.return_value = {"results": []}
            
            payload = {
                "company_description": "ACME",
                "product_details": "App",
                "target_audience": "Users",
                "goals": "Strategy"
            }
            
            result = await research.run("test-job-2", payload)
            
            # Should have done 2 iterations (initial + refinement)
            assert result["iterations"] >= 2


@pytest.mark.asyncio
async def test_strategy_agent_basic_execution():
    """Test strategy agent generates strategic recommendations."""
    from app.agents import strategy
    
    with patch("app.agents.strategy.call_llm") as mock_llm:
        mock_llm.return_value = "# Strategy Report\n\n1. Market positioning..."
        
        payload = {
            "company_description": "ACME",
            "product_details": "App",
            "target_audience": "Users",
            "goals": "GTM",
            "research_report": "Research findings...",
            "memory_context": []
        }
        
        result = await strategy.run("test-job-3", payload)
        
        assert result["status"] == "completed"
        assert "strategy_report" in result
        assert len(result["strategy_report"]) > 0


@pytest.mark.asyncio
async def test_critic_agent_approval():
    """Test critic agent approves good strategy."""
    from app.agents import critic
    
    with patch("app.agents.critic.call_llm") as mock_llm:
        mock_llm.return_value = json.dumps({
            "verdict": "APPROVED",
            "score": 9,
            "issues": [],
            "improvement_prompt": ""
        })
        
        payload = {
            "company_description": "ACME",
            "product_details": "App",
            "research_report": "Research...",
            "strategy_report": "Strategy..."
        }
        
        result = await critic.run("test-job-4", payload)
        
        assert result["verdict"] == "APPROVED"
        assert result["score"] >= 7


@pytest.mark.asyncio
async def test_critic_agent_rejection():
    """Test critic agent rejects weak strategy."""
    from app.agents import critic
    
    with patch("app.agents.critic.call_llm") as mock_llm:
        mock_llm.return_value = json.dumps({
            "verdict": "REJECTED",
            "score": 4,
            "issues": ["Lacks market analysis", "No pricing strategy"],
            "improvement_prompt": "Add competitive pricing analysis"
        })
        
        payload = {
            "company_description": "ACME",
            "product_details": "App",
            "research_report": "Minimal research...",
            "strategy_report": "Weak strategy..."
        }
        
        result = await critic.run("test-job-5", payload)
        
        assert result["verdict"] == "REJECTED"
        assert result["score"] < 7
        assert len(result["issues"]) > 0
        assert len(result["improvement_prompt"]) > 0


@pytest.mark.asyncio
async def test_memory_agent_store_and_recall():
    """Test memory agent stores and recalls context."""
    from app.agents import memory
    
    with patch("app.memory.vector_store.upsert_document") as mock_upsert:
        with patch("app.memory.vector_store.query_similar") as mock_query:
            mock_upsert.return_value = "doc-id-123"
            mock_query.return_value = [
                {
                    "id": "doc-id-123",
                    "document": "Previous research findings...",
                    "metadata": {"source": "research"},
                    "distance": 0.1
                }
            ]
            
            # Test store
            store_payload = {
                "action": "store",
                "content": "Research report content...",
                "source_agent": "research"
            }
            store_result = await memory.run("test-job-6", store_payload)
            assert store_result["status"] == "stored"
            
            # Test recall
            recall_payload = {
                "action": "recall",
                "query": "fitness app research",
                "n_results": 3
            }
            recall_result = await memory.run("test-job-6", recall_payload)
            assert "documents" in recall_result
            assert len(recall_result["documents"]) > 0


@pytest.mark.asyncio
async def test_planner_agent_execution_plan():
    """Test planner agent creates structured execution plan."""
    from app.agents import planner
    
    with patch("app.agents.planner.call_llm") as mock_llm:
        mock_llm.return_value = json.dumps({
            "execution_plan": {
                "phase_30_days": [
                    {
                        "task": "Launch MVP",
                        "owner": "Engineering",
                        "priority": "HIGH",
                        "kpi": "100 users",
                        "dependencies": []
                    }
                ],
                "phase_60_days": [],
                "phase_90_days": []
            },
            "critical_path": ["Launch MVP"],
            "success_metrics": {"30_day": "100 users"}
        })
        
        payload = {
            "company_description": "ACME",
            "product_details": "App",
            "strategy_report": "Strategy..."
        }
        
        result = await planner.run("test-job-7", payload)
        
        assert "execution_plan" in result
        assert "critical_path" in result
        assert "success_metrics" in result


@pytest.mark.asyncio
async def test_qa_agent_validation():
    """Test QA agent validates output quality."""
    from app.agents import qa
    
    with patch("app.agents.qa.call_llm") as mock_llm:
        mock_llm.return_value = json.dumps({
            "passed": True,
            "overall_quality_score": 8,
            "gaps": [],
            "recommendations": []
        })
        
        payload = {
            "company_description": "ACME",
            "product_details": "App",
            "research_report": "Research...",
            "strategy_report": "Strategy...",
            "execution_plan": {
                "execution_plan": {
                    "phase_30_days": [{"task": "t", "owner": "o", "priority": "p", "kpi": "k"}],
                    "phase_60_days": [{"task": "t", "owner": "o", "priority": "p", "kpi": "k"}],
                    "phase_90_days": [{"task": "t", "owner": "o", "priority": "p", "kpi": "k"}]
                },
                "critical_path": ["t"],
                "success_metrics": {"m": "v"}
            }
        }
        
        result = await qa.run("test-job-8", payload)
        
        assert result["passed"] is True
        assert result["overall_quality_score"] >= 6
