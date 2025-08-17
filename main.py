import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Add prompt-toolkit for autocomplete functionality
try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import WordCompleter
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    print("⚠️  prompt-toolkit not available. Install with: uv pip install prompt-toolkit")

class MCPResourceBrowser:
    def __init__(self):
        self.session = None
        self.resources = []
        self.documents = []
        self.prompts = []  # Add prompts list
        self.stdio_client_context = None
        self.session_context = None
    
    async def connect_to_server(self):
        """Connect to the MCP server using proper context management"""
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "/Users/bhogaai/model-context-protocol/mcp_server.py"],
            env=None
        )
        
        # Use proper context management
        self.stdio_client_context = stdio_client(server_params)
        read, write = await self.stdio_client_context.__aenter__()
        
        self.session_context = ClientSession(read, write)
        self.session = await self.session_context.__aenter__()
        await self.session.initialize()
        
        print("✅ Connected to MCP server!")
    
    async def disconnect_from_server(self):
        """Properly disconnect from the MCP server"""
        try:
            if self.session_context:
                await self.session_context.__aexit__(None, None, None)
            if self.stdio_client_context:
                await self.stdio_client_context.__aexit__(None, None, None)
        except Exception as e:
            print(f"⚠️  Warning during disconnect: {e}")
    
    async def load_resources(self):
        """Load available resources from the server"""
        # Get list of resources
        print("🔍 Loading resources...")
        resources_response = await self.session.list_resources()
        self.resources = resources_response.resources
        print(f"📋 Found {len(self.resources)} resources")
        
        # Load prompts
        try:
            prompts_response = await self.session.list_prompts()
            self.prompts = [prompt.name for prompt in prompts_response.prompts]
            print(f"🎯 Found {len(self.prompts)} prompts")
        except Exception as e:
            print(f"⚠️  Error loading prompts: {e}")
            self.prompts = []
        
        # Read docs://documents to get the list of documents
        try:
            docs_response = await self.session.read_resource("docs://documents")
            
            # Parse the JSON response to get document list
            import json
            docs_data = json.loads(docs_response.contents[0].text)
            
            # Handle both list and dictionary formats
            if isinstance(docs_data, list):
                self.documents = docs_data
            elif isinstance(docs_data, dict):
                self.documents = docs_data.get('documents', [])
            else:
                print(f"⚠️  Unexpected data format: {type(docs_data)}")
                self.documents = []
            
            print(f"📄 Found {len(self.documents)} documents")
            
        except Exception as e:
            print(f"❌ Error loading documents: {e}")
            import traceback
            print(f"📍 Debug traceback: {traceback.format_exc()}")
            self.documents = []
    
    def display_resources(self):
        """Display available resources"""
        if self.documents:
            print("\n📋 Available documents:")
            for i, doc in enumerate(self.documents, 1):
                print(f"  {i}. @{doc}")
        else:
            print("❌ No documents available")
        
        if self.prompts:
            print("\n🎯 Available prompts:")
            for i, prompt in enumerate(self.prompts, 1):
                print(f"  {i}. /{prompt}")
        else:
            print("❌ No prompts available")
            print("💡 Try running the server manually to check for issues")
            return
        
        print("\n📋 Available Documents:")
        print("=" * 40)
        for doc in self.documents:
            print(f"  📄 @{doc}")
        print("=" * 40)
        print("💡 Usage: Type '@document_name' to read a document")
        print("💡 Usage: Type '@' and press Tab for autocomplete suggestions")
    
    async def read_resource_content(self, document_name):
        """Read and display the content of a specific document"""
        try:
            print(f"\n📖 Reading document: {document_name}")
            print("=" * 50)
            
            # Read the document content - use correct URI format
            resource_uri = f"docs://documents/{document_name}"
            response = await self.session.read_resource(resource_uri)
            
            # Display the content
            for content in response.contents:
                if hasattr(content, 'text'):
                    print(content.text)
                else:
                    print(f"Content type: {type(content)}")
                    print(content)
            
            print("\n" + "=" * 50)
            
        except Exception as e:
            print(f"❌ Error reading document '{document_name}': {e}")
            print(f"💡 Available documents: {', '.join(['@' + doc for doc in self.documents])}")
    
    async def use_prompt(self, prompt_name, **kwargs):
        """Use a specific prompt"""
        try:
            prompt_result = await self.session.get_prompt(prompt_name, arguments=kwargs)
            print(f"\n🎯 Prompt '{prompt_name}' result:")
            print("=" * 50)
            for message in prompt_result.messages:
                print(f"Role: {message.role}")
                print(f"Content: {message.content.text}")
                print("-" * 30)
            print("=" * 50)
        except Exception as e:
            print(f"❌ Error using prompt '{prompt_name}': {e}")
            print(f"💡 Available prompts: {', '.join(['/' + prompt for prompt in self.prompts])}")
    
    async def process_command(self, command):
        """Process user commands"""
        import re
        command = command.strip()
        
        if command.lower() in ['quit', 'exit', 'q']:
            return False
        
        elif command == '@':
            # Just display resources - autocomplete handles selection
            self.display_resources()
        
        elif command == '/':
            # Display prompts
            if self.prompts:
                print("\n🎯 Available prompts:")
                for i, prompt in enumerate(self.prompts, 1):
                    print(f"  {i}. /{prompt}")
            else:
                print("❌ No prompts available")
            
        elif command.startswith('@'):
            document_name = command[1:]  # Remove @ prefix
            if document_name in self.documents:
                await self.read_resource_content(document_name)
            else:
                print(f"❌ Document '@{document_name}' not found")
                print(f"💡 Available documents: {', '.join(['@' + doc for doc in self.documents])}")
        
        elif command.startswith('/'):
            prompt_name = command[1:]  # Remove / prefix
            if prompt_name in self.prompts:
                # Handle prompts that require arguments
                if prompt_name == 'format_doc_prompt':
                    # Ask user for document ID or use first available document
                    print(f"📝 Using prompt '{prompt_name}' - requires document ID:")
                    print(f"💡 Available documents: {', '.join(self.documents)}")
                    # For demo, use first document if available
                    if self.documents:
                        doc_id = self.documents[0]
                        print(f"🎯 Using document: {doc_id}")
                        await self.use_prompt(prompt_name, doc_id=doc_id)
                    else:
                        print("❌ No documents available for formatting")
                else:
                    await self.use_prompt(prompt_name)
            else:
                print(f"❌ Prompt '/{prompt_name}' not found")
                print(f"💡 Available prompts: {', '.join(['/' + prompt for prompt in self.prompts])}")
        
        elif command == '':
            pass  # Empty command, do nothing
            
        else:
            # Check if the command contains any @document_name or /prompt_name patterns
            document_pattern = r'@([a-zA-Z0-9_.-]+(?:\.[a-zA-Z0-9]+)?)'  # Matches @filename.ext
            prompt_pattern = r'/([a-zA-Z0-9_-]+)'  # Matches /prompt_name
            
            doc_matches = re.findall(document_pattern, command)
            prompt_matches = re.findall(prompt_pattern, command)
            
            if doc_matches or prompt_matches:
                if doc_matches:
                    print(f"📝 Found document references: {', '.join(['@' + match for match in doc_matches])}")
                    for document_name in doc_matches:
                        if document_name in self.documents:
                            print(f"\n📄 Reading document: @{document_name}")
                            await self.read_resource_content(document_name)
                        else:
                            print(f"❌ Document '@{document_name}' not found")
                
                if prompt_matches:
                    print(f"🎯 Found prompt references: {', '.join(['/' + match for match in prompt_matches])}")
                    for prompt_name in prompt_matches:
                        if prompt_name in self.prompts:
                            print(f"\n🎯 Using prompt: /{prompt_name}")
                            await self.use_prompt(prompt_name)
                        else:
                            print(f"❌ Prompt '/{prompt_name}' not found")
            else:
                print(f"❓ Unknown command: {command}")
                print("💡 Use '@' for documents, '/' for prompts, or 'quit' to exit")
        
        return True
    
    async def get_input_with_autocomplete(self):
        """Get user input with autocomplete functionality (async version)"""
        if PROMPT_TOOLKIT_AVAILABLE and (self.documents or self.prompts):
            from prompt_toolkit.completion import Completer, Completion
            from prompt_toolkit.shortcuts import PromptSession
            from prompt_toolkit.document import Document
            
            class ResourceCompleter(Completer):
                def __init__(self, documents, prompts):
                    self.documents = documents
                    self.prompts = prompts
                
                def get_completions(self, document, complete_event):
                    # Get the text before the cursor
                    text_before_cursor = document.text_before_cursor
                    
                    # Check for '@' (documents)
                    at_index = text_before_cursor.rfind('@')
                    slash_index = text_before_cursor.rfind('/')
                    
                    # Determine which trigger is more recent
                    if at_index != -1 and (slash_index == -1 or at_index > slash_index):
                        # Handle document completion
                        partial_text = text_before_cursor[at_index + 1:]
                        
                        for doc in self.documents:
                            if doc.lower().startswith(partial_text.lower()):
                                start_position = -len(partial_text)
                                yield Completion(
                                    text=doc,
                                    start_position=start_position,
                                    display=f"@{doc}"
                                )
                        
                        if not partial_text:
                            for doc in self.documents:
                                yield Completion(
                                    text=doc,
                                    start_position=0,
                                    display=f"@{doc}"
                                )
                    
                    elif slash_index != -1 and (at_index == -1 or slash_index > at_index):
                        # Handle prompt completion
                        partial_text = text_before_cursor[slash_index + 1:]
                        
                        for prompt in self.prompts:
                            if prompt.lower().startswith(partial_text.lower()):
                                start_position = -len(partial_text)
                                yield Completion(
                                    text=prompt,
                                    start_position=start_position,
                                    display=f"/{prompt}"
                                )
                        
                        if not partial_text:
                            for prompt in self.prompts:
                                yield Completion(
                                    text=prompt,
                                    start_position=0,
                                    display=f"/{prompt}"
                                )
            
            completer = ResourceCompleter(self.documents, self.prompts)
            session = PromptSession(completer=completer, complete_while_typing=True)
            
            try:
                result = await session.prompt_async("> ")
                return result.strip()
            except (KeyboardInterrupt, EOFError):
                raise
        else:
            # Fallback to regular input (need to run in executor for async)
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, input, "> ")
            return result.strip()
    
    async def run_interactive_mode(self):
        """Run the interactive resource browser with autocomplete"""
        print("\n🚀 MCP Resource Browser")
        print("=" * 40)
        
        try:
            await self.connect_to_server()
            await self.load_resources()
            
            self.display_resources()
            
            if PROMPT_TOOLKIT_AVAILABLE:
                print("\n🎯 Interactive Mode Started (with autocomplete)")
                print("Type '@' and press Tab to see suggestions:")
            else:
                print("\n🎯 Interactive Mode Started")
                print("Install prompt-toolkit for autocomplete: uv pip install prompt-toolkit")
            
            while True:
                try:
                    command = await self.get_input_with_autocomplete()  # Add await here
                    
                    if not await self.process_command(command):
                        break
                        
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                except EOFError:
                    print("\n\n👋 Goodbye!")
                    break
                    
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            print(f"📍 Traceback: {traceback.format_exc()}")
        
        finally:
            print("\n🔌 Disconnecting from server...")
            await self.disconnect_from_server()
    
    async def run_command_mode(self, command):
        """Run a single command and exit"""
        try:
            await self.connect_to_server()
            await self.load_resources()
            await self.process_command(command)
        finally:
            await self.disconnect_from_server()

async def main():
    """Main function"""
    browser = MCPResourceBrowser()
    
    if len(sys.argv) > 1:
        # Command mode - run a single command
        command = ' '.join(sys.argv[1:])
        await browser.run_command_mode(command)
    else:
        # Interactive mode
        await browser.run_interactive_mode()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"📍 Traceback: {traceback.format_exc()}")