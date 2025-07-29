# apps/backend/tests/test_multiagent_system.py

import unittest
import asyncio
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any
import tempfile
import os

# Import the modules we're testing
from app.env.grid import Grid, TerrainType, ResourceType
from app.agents.base import BaseAgent, MemoryType
from app.agents.scout import ScoutAgent
from app.agents.builder import BuilderAgent
from app.agents.strategist import StrategistAgent
from app.tools.message import Message, MessageType, MessagePriority
from app.tools.message_queue import CoordinationManager, SharedState
from app.langgraph.agent_flow import build_agent_flow, AgentState
from app.utils.error_handling import ErrorRecoveryManager, ErrorCategory, ErrorSeverity

class TestGrid(unittest.TestCase):
    """Test grid operations and terrain system"""
    
    def setUp(self):
        self.grid = Grid(5, 5, terrain_seed=42)  # Fixed seed for reproducible tests
    
    def test_grid_initialization(self):
        """Test grid is properly initialized"""
        self.assertEqual(self.grid.width, 5)
        self.assertEqual(self.grid.height, 5)
        self.assertEqual(len(self.grid.grid), 25)
    
    def test_agent_placement(self):
        """Test agent placement and position tracking"""
        success = self.grid.place_agent("test_agent", (0, 0))
        self.assertTrue(success)
        self.assertEqual(self.grid.get_agent_position("test_agent"), (0, 0))
        
        # Test placement on occupied cell
        success2 = self.grid.place_agent("test_agent2", (0, 0))
        self.assertFalse(success2)
    
    def test_movement_with_collision_avoidance(self):
        """Test movement system with collision avoidance"""
        self.grid.place_agent("agent1", (0, 0))
        self.grid.place_agent("agent2", (1, 0))
        
        # Both agents try to move to same location
        self.grid.request_movement("agent1", (2, 0), priority=1.0)
        self.grid.request_movement("agent2", (2, 0), priority=0.5)
        
        results = self.grid.execute_movements()
        
        # Higher priority agent should succeed
        self.assertTrue(results["agent1"])
        self.assertFalse(results["agent2"])
        self.assertEqual(self.grid.get_agent_position("agent1"), (2, 0))
        self.assertEqual(self.grid.get_agent_position("agent2"), (1, 0))
    
    def test_resource_management(self):
        """Test resource harvesting and regeneration"""
        # Find a resource-rich cell
        resource_cell = None
        for pos, cell in self.grid.grid.items():
            if cell.terrain.resources:
                resource_cell = pos
                break
        
        if resource_cell:
            # Test resource harvesting
            initial_amount = list(cell.terrain.resources.values())[0].amount
            resource_type = list(cell.terrain.resources.keys())[0]
            
            harvested = self.grid.harvest_resources(resource_cell, resource_type, 5, "test_agent")
            self.assertGreater(harvested, 0)
            self.assertLessEqual(harvested, 5)
    
    def test_pathfinding_with_terrain(self):
        """Test pathfinding considers terrain costs"""
        path = self.grid.find_path_with_terrain((0, 0), (4, 4))
        self.assertIsInstance(path, list)
        if path:  # Path found
            self.assertEqual(path[0], (0, 0))
            self.assertEqual(path[-1], (4, 4))

class TestAgentMemorySystem(unittest.TestCase):
    """Test agent memory and learning systems"""
    
    def setUp(self):
        self.grid = Grid(3, 3)
        self.shared_state = SharedState()
        self.coordination_manager = CoordinationManager(self.shared_state)
        
        # Mock OpenAI client to avoid API calls in tests
        with patch('openai.OpenAI'):
            self.agent = ScoutAgent("test_scout", self.grid, self.coordination_manager, self.shared_state)
    
    def test_memory_storage_and_retrieval(self):
        """Test memory system stores and retrieves correctly"""
        self.agent._store_memory("Test memory", MemoryType.SHORT_TERM, importance=0.8)
        
        memories = self.agent._retrieve_memories("Test", MemoryType.SHORT_TERM)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0].content, "Test memory")
        self.assertEqual(memories[0].importance, 0.8)
    
    def test_memory_pruning(self):
        """Test memory system prunes old/unimportant memories"""
        # Fill memory with low-importance entries
        for i in range(100):
            self.agent._store_memory(f"Low importance {i}", MemoryType.SHORT_TERM, importance=0.1)
        
        # Add a high-importance memory
        self.agent._store_memory("Important memory", MemoryType.SHORT_TERM, importance=0.9)
        
        # Trigger pruning by adding more memories
        for i in range(50):
            self.agent._store_memory(f"New memory {i}", MemoryType.SHORT_TERM, importance=0.5)
        
        # Important memory should still be there
        memories = self.agent._retrieve_memories("Important", MemoryType.SHORT_TERM)
        self.assertTrue(any(m.content == "Important memory" for m in memories))
    
    def test_planning_system(self):
        """Test multi-step planning capabilities"""
        plan = self.agent.planning_system.create_plan("explore the area", {})
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        
        # Test plan execution
        next_step = self.agent.planning_system.execute_next_step()
        self.assertIsInstance(next_step, dict)
        self.assertIn("action", next_step)

class TestMessageQueueSystem(unittest.TestCase):
    """Test message queue and coordination systems"""
    
    def setUp(self):
        self.shared_state = SharedState()
        self.coordination_manager = CoordinationManager(self.shared_state)
    
    def test_message_priority_queue(self):
        """Test messages are processed by priority"""
        low_msg = Message("agent1", "agent2", "Low priority", priority=MessagePriority.LOW)
        high_msg = Message("agent1", "agent2", "High priority", priority=MessagePriority.HIGH)
        
        self.coordination_manager.send_message(low_msg)
        self.coordination_manager.send_message(high_msg)
        
        # High priority message should come first
        messages = self.coordination_manager.get_messages_for_agent("agent2")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].priority, MessagePriority.HIGH)
    
    def test_message_acknowledgment(self):
        """Test message acknowledgment system"""
        msg = Message("agent1", "agent2", "Test", requires_ack=True)
        self.coordination_manager.send_message(msg)
        
        # Get message and acknowledge
        messages = self.coordination_manager.get_messages_for_agent("agent2")
        self.assertEqual(len(messages), 1)
        
        ack_success = self.coordination_manager.message_queue.acknowledge(msg.message_id, "agent2")
        self.assertTrue(ack_success)
    
    def test_shared_state_resource_allocation(self):
        """Test shared state resource management"""
        # Initialize resources
        self.shared_state.resources["materials"] = 100
        
        # Test allocation
        success = self.shared_state.allocate_resource("agent1", "materials", 30)
        self.assertTrue(success)
        self.assertEqual(self.shared_state.resources["materials"], 70)
        
        # Test over-allocation
        success2 = self.shared_state.allocate_resource("agent2", "materials", 80)
        self.assertFalse(success2)
        
        # Test resource release
        self.shared_state.release_resource("agent1", "materials", 20)
        self.assertEqual(self.shared_state.resources["materials"], 90)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and recovery systems"""
    
    def setUp(self):
        self.error_manager = ErrorRecoveryManager()
    
    def test_error_handling(self):
        """Test error handling and recovery"""
        test_error = ValueError("Test error")
        
        success = self.error_manager.handle_error(
            test_error, 
            ErrorCategory.AGENT_LOGIC, 
            ErrorSeverity.MEDIUM,
            {"test": "context"}
        )
        
        self.assertIsInstance(success, bool)
        self.assertEqual(len(self.error_manager.error_history), 1)
        
        error_event = self.error_manager.error_history[0]
        self.assertEqual(error_event.category, ErrorCategory.AGENT_LOGIC)
        self.assertEqual(error_event.severity, ErrorSeverity.MEDIUM)
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        cb = self.error_manager.get_circuit_breaker("test_service")
        
        # Function that always fails
        def failing_function():
            raise Exception("Always fails")
        
        # Should fail and eventually open circuit
        for _ in range(6):  # More than failure threshold
            try:
                cb.call(failing_function)
            except:
                pass
        
        self.assertEqual(cb.state, "OPEN")
    
    def test_retry_strategy(self):
        """Test retry strategies"""
        from app.utils.error_handling import RetryStrategy
        
        retry_strategy = RetryStrategy(max_retries=2, base_delay=0.1)
        
        # Function that succeeds on third try
        self.attempt_count = 0
        def flaky_function():
            self.attempt_count += 1
            if self.attempt_count < 3:
                raise Exception("Not yet")
            return "success"
        
        result = retry_strategy.execute(flaky_function)
        self.assertEqual(result, "success")
        self.assertEqual(self.attempt_count, 3)

class TestLangGraphFlow(unittest.TestCase):
    """Test LangGraph workflow and conditional routing"""
    
    def setUp(self):
        self.grid = Grid(3, 3)
        
        # Mock the flow to avoid complex initialization
        self.mock_state = {
            "grid": self.grid,
            "messages": [],
            "step_count": 0,
            "mission_phase": "initialization",
            "objectives": [],
            "exploration_progress": 0.0,
            "buildings_built": 0,
            "active_threats": 0,
            "resource_constraints": False,
            "coordination_needed": False,
            "emergency_mode": False,
            "last_activity": {"scout": "none", "strategist": "none", "builder": "none"},
            "strategic_plan_ready": False,
            "shared_state": SharedState(),
            "coordination_manager": CoordinationManager(SharedState()),
            "agent_states": {},
            "error_recovery_attempts": 0,
            "performance_metrics": {},
            "parallel_execution_enabled": True
        }
    
    def test_conditional_routing(self):
        """Test conditional routing logic"""
        from app.langgraph.agent_flow import route_next_action
        
        # Test initialization phase routing
        route = route_next_action(self.mock_state)
        self.assertEqual(route, "initialization_phase")
        
        # Test exploration phase routing
        self.mock_state["mission_phase"] = "exploration"
        route = route_next_action(self.mock_state)
        self.assertEqual(route, "exploration_phase")
        
        # Test emergency routing
        self.mock_state["emergency_mode"] = True
        route = route_next_action(self.mock_state)
        self.assertEqual(route, "emergency_response")
    
    def test_state_updates(self):
        """Test state update mechanisms"""
        from app.langgraph.agent_flow import update_state_metrics
        
        initial_step_count = self.mock_state["step_count"]
        updated_state = update_state_metrics(self.mock_state)
        
        # State should be updated
        self.assertIsInstance(updated_state, dict)
        self.assertIn("exploration_progress", updated_state)

class TestPerformanceAndScalability(unittest.TestCase):
    """Test performance characteristics and scalability"""
    
    def test_grid_performance(self):
        """Test grid operations scale reasonably"""
        start_time = time.time()
        
        # Create larger grid
        large_grid = Grid(50, 50)
        
        # Place many agents
        for i in range(100):
            large_grid.place_agent(f"agent_{i}", (i % 50, i // 50))
        
        # Perform many movements
        for i in range(100):
            agent_id = f"agent_{i}"
            pos = large_grid.get_agent_position(agent_id)
            if pos:
                new_x = (pos[0] + 1) % 50
                large_grid.request_movement(agent_id, (new_x, pos[1]))
        
        large_grid.execute_movements()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(execution_time, 5.0, "Grid operations took too long")
    
    def test_memory_usage(self):
        """Test memory usage doesn't grow unbounded"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create agents and run many operations
        grid = Grid(10, 10)
        shared_state = SharedState()
        coordination_manager = CoordinationManager(shared_state)
        
        with patch('openai.OpenAI'):
            agents = []
            for i in range(10):
                agent = ScoutAgent(f"scout_{i}", grid, coordination_manager, shared_state)
                agents.append(agent)
        
        # Run many operations
        for _ in range(100):
            for agent in agents:
                agent._store_memory(f"Memory entry {_}", MemoryType.SHORT_TERM)
                agent.observe()
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for this test)
        self.assertLess(memory_growth, 100 * 1024 * 1024, "Excessive memory growth detected")
    
    def test_concurrent_operations(self):
        """Test system handles concurrent operations correctly"""
        grid = Grid(5, 5)
        shared_state = SharedState()
        coordination_manager = CoordinationManager(shared_state)
        
        # Initialize resources
        shared_state.resources["materials"] = 1000
        
        results = []
        errors = []
        
        def worker_thread(thread_id):
            try:
                # Each thread tries to allocate resources
                success = shared_state.allocate_resource(f"agent_{thread_id}", "materials", 10)
                results.append((thread_id, success))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(20):  # More threads than resources allow
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have no errors (thread-safe)
        self.assertEqual(len(errors), 0, f"Concurrent operations caused errors: {errors}")
        
        # Should not over-allocate resources
        total_allocated = sum(
            shared_state.get_agent_resources(f"agent_{i}").get("materials", 0) 
            for i in range(20)
        )
        self.assertLessEqual(total_allocated, 1000, "Over-allocation detected")

class PropertyBasedTestGrid(unittest.TestCase):
    """Property-based testing for grid operations"""
    
    def test_movement_invariants(self):
        """Test movement preserves important invariants"""
        grid = Grid(10, 10)
        
        # Property: After placing an agent, it should be findable
        for i in range(50):  # Test with random positions
            x, y = i % 10, i // 10
            if grid.is_empty(x, y):
                agent_id = f"agent_{i}"
                success = grid.place_agent(agent_id, (x, y))
                if success:
                    found_pos = grid.get_agent_position(agent_id)
                    self.assertEqual(found_pos, (x, y), 
                                   f"Agent {agent_id} not found at expected position")
    
    def test_resource_conservation(self):
        """Test resources are conserved (not created or destroyed inappropriately)"""
        grid = Grid(5, 5, terrain_seed=42)
        
        # Calculate initial total resources
        initial_total = {}
        for cell in grid.grid.values():
            for resource_type, deposit in cell.terrain.resources.items():
                rt_key = resource_type.value
                initial_total[rt_key] = initial_total.get(rt_key, 0) + deposit.amount
        
        # Harvest some resources
        harvested_total = {}
        for pos, cell in grid.grid.items():
            for resource_type, deposit in cell.terrain.resources.items():
                if deposit.amount > 0:
                    harvested = grid.harvest_resources(pos, resource_type, 5, "test_agent")
                    rt_key = resource_type.value
                    harvested_total[rt_key] = harvested_total.get(rt_key, 0) + harvested
        
        # Calculate remaining resources
        remaining_total = {}
        for cell in grid.grid.values():
            for resource_type, deposit in cell.terrain.resources.items():
                rt_key = resource_type.value
                remaining_total[rt_key] = remaining_total.get(rt_key, 0) + deposit.amount
        
        # Conservation check: initial = remaining + harvested
        for rt_key in initial_total:
            total_accounted = (remaining_total.get(rt_key, 0) + 
                             harvested_total.get(rt_key, 0))
            self.assertEqual(initial_total[rt_key], total_accounted,
                           f"Resource conservation violated for {rt_key}")

class IntegrationTests(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        self.grid = Grid(6, 5)
        
    @patch('openai.OpenAI')
    def test_full_simulation_cycle(self, mock_openai):
        """Test a complete simulation cycle"""
        # Mock LLM responses
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "MOVE north"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Initialize system
        from app.simulation import Simulation
        sim = Simulation(width=6, height=5)
        
        # Run several simulation steps
        for i in range(5):
            result = sim.step()
            
            # Verify basic structure
            self.assertIn("logs", result)
            self.assertIn("grid", result)
            self.assertIn("agents", result)
            self.assertIn("step_count", result)
            self.assertEqual(result["step_count"], i + 1)
            
            # Verify agents are functioning
            self.assertGreater(len(result["agents"]), 0)
    
    @patch('openai.OpenAI')
    def test_error_recovery_integration(self, mock_openai):
        """Test error recovery in integrated system"""
        # Setup mock to sometimes fail
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                raise Exception("Simulated API failure")
            
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "WAIT"
            return mock_response
        
        mock_client.chat.completions.create.side_effect = side_effect
        
        # Initialize system with error handling
        from app.utils.error_handling import initialize_error_handling
        initialize_error_handling()
        
        from app.simulation import Simulation
        sim = Simulation(width=3, 3)
        
        # Run simulation - should handle errors gracefully
        error_count = 0
        for i in range(10):
            try:
                result = sim.step()
                # Should still get valid results despite some failures
                self.assertIn("step_count", result)
            except Exception as e:
                error_count += 1
        
        # Some errors expected, but not all operations should fail
        self.assertLess(error_count, 5, "Too many unhandled errors")
    
    def test_performance_under_load(self):
        """Test system performance under load"""
        import time
        
        start_time = time.time()
        
        # Create larger system
        grid = Grid(20, 20)
        shared_state = SharedState()
        coordination_manager = CoordinationManager(shared_state)
        
        # Add resources
        for resource_type in ["materials", "energy", "tools"]:
            shared_state.resources[resource_type] = 1000
        
        # Simulate heavy load
        with patch('openai.OpenAI'):
            agents = []
            for i in range(50):  # Many agents
                if i % 3 == 0:
                    agent = ScoutAgent(f"scout_{i}", grid, coordination_manager, shared_state)
                elif i % 3 == 1:
                    agent = BuilderAgent(f"builder_{i}", grid, coordination_manager, shared_state)
                else:
                    agent = StrategistAgent(f"strategist_{i}", grid, coordination_manager, shared_state)
                agents.append(agent)
                
                # Place agent
                x, y = i % 20, i // 20
                if grid.is_empty(x, y):
                    grid.place_agent(agent.agent_id, (x, y))
        
        # Simulate many operations
        for step in range(10):
            # Each agent performs operations
            for agent in agents:
                try:
                    # Simulate agent step
                    messages = coordination_manager.get_messages_for_agent(agent.agent_id)
                    agent.observe()
                    agent._store_memory(f"Step {step}", MemoryType.SHORT_TERM)
                    
                    # Resource operations
                    shared_state.allocate_resource(agent.agent_id, "materials", 1)
                    
                except Exception as e:
                    # Some failures acceptable under load
                    pass
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time
        self.assertLess(total_time, 30.0, f"Load test took too long: {total_time}s")

class TestSuite:
    """Main test suite runner"""
    
    @staticmethod
    def run_all_tests():
        """Run all test suites"""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add all test classes
        test_classes = [
            TestGrid,
            TestAgentMemorySystem, 
            TestMessageQueueSystem,
            TestErrorHandling,
            TestLangGraphFlow,
            TestPerformanceAndScalability,
            PropertyBasedTestGrid,
            IntegrationTests
        ]
        
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    
    @staticmethod
    def run_performance_tests():
        """Run only performance-related tests"""
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add performance test classes
        performance_classes = [
            TestPerformanceAndScalability,
            PropertyBasedTestGrid
        ]
        
        for test_class in performance_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)
    
    @staticmethod 
    def run_integration_tests():
        """Run only integration tests"""
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(IntegrationTests)
        
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)

# Additional utility functions for testing
def create_test_environment():
    """Create a test environment with mocked external dependencies"""
    with patch('openai.OpenAI') as mock_openai:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "WAIT"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        yield mock_openai, mock_client

def assert_agent_state_valid(agent, test_case):
    """Assert that an agent is in a valid state"""
    test_case.assertIsNotNone(agent.agent_id)
    test_case.assertIsNotNone(agent.role)
    test_case.assertIsNotNone(agent.status)
    test_case.assertIsInstance(agent.memory_system.memories, dict)
    test_case.assertIsInstance(agent.tools, dict)

def assert_grid_state_valid(grid, test_case):
    """Assert that a grid is in a valid state"""
    test_case.assertGreater(grid.width, 0)
    test_case.assertGreater(grid.height, 0)
    test_case.assertEqual(len(grid.grid), grid.width * grid.height)
    
    # Check agent position consistency
    for agent_id, position in grid.agent_positions.items():
        cell = grid.grid.get(position)
        test_case.assertIsNotNone(cell)
        test_case.assertEqual(cell.occupied_by, agent_id)

def benchmark_operation(operation, *args, **kwargs):
    """Benchmark an operation and return execution time"""
    start_time = time.time()
    result = operation(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

if __name__ == "__main__":
    # Run all tests when script is executed directly
    print("Running comprehensive multiagent system tests...")
    result = TestSuite.run_all_tests()
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")