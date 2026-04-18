import asyncio
import sys

# Import our autonomous orchestration agents
from app.adk.agents import coordinator_agent

async def interactive_cli():
    print("==================================================")
    print(" Vectorless RAG Agent Interface (Google ADK) ")
    print("==================================================")
    print("Secure Multi-Tenant Context Active.")
    print("Type 'exit' or 'quit' to close the session.\n")
    
    while True:
        try:
            user_input = input("User >> ")
            if user_input.strip().lower() in ['exit', 'quit']:
                print("Exiting ADK Agent Interface. Goodbye.")
                break
                
            if not user_input.strip():
                continue
                
            print("\nCoordinatorAgent << Processing...")
            
            # Execute the ADK workflow dynamically using Vectorless Skills
            response = await coordinator_agent.run(user_input)
            
            print(f"\nAgent >>\n{response}\n")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nExiting ADK Agent Interface immediately.")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as e:
            print(f"\n[Error executing Agent Trajectory] {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(interactive_cli())
