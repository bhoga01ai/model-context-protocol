import streamlit as st
import sys
import os
import subprocess
import json
import re
from streamlit_ace import st_ace

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(
    page_title="MCP Resource Browser",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'resources' not in st.session_state:
    st.session_state.resources = []
if 'prompts' not in st.session_state:
    st.session_state.prompts = []
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""
if 'show_suggestions' not in st.session_state:
    st.session_state.show_suggestions = False
if 'current_suggestions' not in st.session_state:
    st.session_state.current_suggestions = []
if 'suggestion_type' not in st.session_state:
    st.session_state.suggestion_type = ""
if 'text_area_content' not in st.session_state:
    st.session_state.text_area_content = ""
if 'command_history' not in st.session_state:
    st.session_state.command_history = []
if 'show_output' not in st.session_state:
    st.session_state.show_output = False
if 'last_output' not in st.session_state:
    st.session_state.last_output = ""
if 'last_command' not in st.session_state:
    st.session_state.last_command = ""
if 'selected_resource' not in st.session_state:
    st.session_state.selected_resource = None

def get_resources():
    """Get resources from MCP server using subprocess"""
    try:
        # Use 'help' command to trigger connection and resource loading
        result = subprocess.run(
            [sys.executable, 'main.py', 'help'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.returncode == 0:
            # Parse the output to extract resources
            lines = result.stdout.strip().split('\n')
            resources = []
            prompts = []
            documents = []
            
            # Look for resource information in the output
            for line in lines:
                # Extract documents from lines like "📄 @document_name"
                if line.strip().startswith('📄 @'):
                    doc_name = line.strip().replace('📄 @', '')
                    documents.append(doc_name)
                # Extract documents from lines like "@document_name"
                elif line.strip().startswith('@'):
                    doc_name = line.strip()[1:]  # Remove @
                    if doc_name and doc_name not in documents:
                        documents.append(doc_name)
            
            # Try to get prompts by running a list command
            try:
                prompt_result = subprocess.run(
                    [sys.executable, 'main.py', 'list prompts'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if prompt_result.returncode == 0:
                    prompt_lines = prompt_result.stdout.strip().split('\n')
                    for line in prompt_lines:
                        if line.strip().startswith('/'):
                            prompt_name = line.strip()[1:]  # Remove /
                            if prompt_name:
                                prompts.append(prompt_name)
            except:
                pass
            
            # If we didn't get documents from help, try list documents
            if not documents:
                try:
                    doc_result = subprocess.run(
                        [sys.executable, 'main.py', 'list documents'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if doc_result.returncode == 0:
                        doc_lines = doc_result.stdout.strip().split('\n')
                        for line in doc_lines:
                            if line.strip().startswith('@'):
                                doc_name = line.strip()[1:]  # Remove @
                                if doc_name:
                                    documents.append(doc_name)
                except:
                    pass
            
            # Fallback: try to extract from any @ or / mentions in output
            if not documents and not prompts:
                all_text = result.stdout
                # Find @mentions
                doc_matches = re.findall(r'@([a-zA-Z0-9_.-]+)', all_text)
                documents.extend(list(set(doc_matches)))
                
                # Find /mentions  
                prompt_matches = re.findall(r'/([a-zA-Z0-9_.-]+)', all_text)
                prompts.extend(list(set(prompt_matches)))
            
            return True, resources, prompts, documents
        else:
            st.error(f"Failed to connect: {result.stderr}")
            return False, [], [], []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return False, [], [], []

def execute_command(command):
    """Execute a command using the MCP server and return formatted result"""
    try:
        result = subprocess.run(
            [sys.executable, 'main.py', command],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
        
        # Format the command and output for inline display
        formatted_result = f"\n\n--- Command Executed ---\n> {command}\n\n--- Output ---\n{output}\n{'-'*50}\n"
        
        return output, formatted_result
    except Exception as e:
        error_msg = f"Execution error: {str(e)}"
        formatted_result = f"\n\n--- Command Executed ---\n> {command}\n\n--- Error ---\n{error_msg}\n{'-'*50}\n"
        return error_msg, formatted_result

def get_real_time_suggestions(text):
    """Get real-time autocomplete suggestions based on current text"""
    if not st.session_state.connected or not text:
        return [], ""
    
    # Find the last @ or / in the text
    cursor_pos = len(text)
    text_before_cursor = text[:cursor_pos]
    
    # Check for @ (documents)
    at_matches = list(re.finditer(r'@([^\s]*)', text_before_cursor))
    if at_matches:
        last_at = at_matches[-1]
        if last_at.end() == cursor_pos or (last_at.end() <= cursor_pos and not text[last_at.end():cursor_pos].strip()):
            prefix = last_at.group(1).lower()
            suggestions = [doc for doc in st.session_state.documents if doc.lower().startswith(prefix)]
            return suggestions, "document"
    
    # Check for / (prompts)
    slash_matches = list(re.finditer(r'/([^\s]*)', text_before_cursor))
    if slash_matches:
        last_slash = slash_matches[-1]
        if last_slash.end() == cursor_pos or (last_slash.end() <= cursor_pos and not text[last_slash.end():cursor_pos].strip()):
            prefix = last_slash.group(1).lower()
            suggestions = [prompt for prompt in st.session_state.prompts if prompt.lower().startswith(prefix)]
            return suggestions, "prompt"
    
    return [], ""

def apply_suggestion(suggestion, suggestion_type):
    """Apply a suggestion to the current input"""
    current_text = st.session_state.current_input
    
    if suggestion_type == "document":
        # Find the last @ and replace everything after it
        at_matches = list(re.finditer(r'@([^\s]*)', current_text))
        if at_matches:
            last_at = at_matches[-1]
            new_text = current_text[:last_at.start()] + f"@{suggestion}" + current_text[last_at.end():]
            st.session_state.current_input = new_text
    elif suggestion_type == "prompt":
        # Find the last / and replace everything after it
        slash_matches = list(re.finditer(r'/([^\s]*)', current_text))
        if slash_matches:
            last_slash = slash_matches[-1]
            new_text = current_text[:last_slash.start()] + f"/{suggestion}" + current_text[last_slash.end():]
            st.session_state.current_input = new_text
    
    # Clear suggestions
    st.session_state.show_suggestions = False
    st.session_state.current_suggestions = []

# Create main layout with sidebar
with st.sidebar:
    st.title("🔍 MCP Resources")
    
    # Connection section
    st.header("🔌 Connection")
    if st.button("Connect to MCP Server", type="primary", use_container_width=True):
        with st.spinner("Connecting..."):
            success, resources, prompts, documents = get_resources()
            if success:
                st.session_state.connected = True
                st.session_state.resources = resources
                st.session_state.prompts = prompts
                st.session_state.documents = documents
                st.success("Connected successfully!")
                st.rerun()
            else:
                st.error("Failed to connect to MCP server")
    
    if st.session_state.connected:
        st.success("✅ Connected")
        st.caption(f"Resources: {len(st.session_state.resources)} | Prompts: {len(st.session_state.prompts)} | Documents: {len(st.session_state.documents)}")
    else:
        st.error("❌ Not connected")
    
    st.divider()
    
    # Enhanced Resource Browser (like in your image)
    if st.session_state.connected:
        st.header("📚 Resource Browser")
        
        # Documents section with enhanced styling
        if st.session_state.documents:
            st.subheader("📄 Documents")
            with st.container():
                for i, doc in enumerate(st.session_state.documents):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Create clickable document entries
                        if st.button(
                            f"📄 {doc}", 
                            key=f"doc_btn_{i}",
                            use_container_width=True,
                            help=f"Click to read {doc}"
                        ):
                            st.session_state.current_input = f"@{doc}"
                            st.session_state.selected_resource = doc
                            st.rerun()
                    with col2:
                        st.caption("Resource")
        
        st.divider()
        
        # Prompts section
        if st.session_state.prompts:
            st.subheader("💬 Prompts")
            with st.container():
                for i, prompt in enumerate(st.session_state.prompts):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(
                            f"💬 {prompt}", 
                            key=f"prompt_btn_{i}",
                            use_container_width=True,
                            help=f"Click to use {prompt} prompt"
                        ):
                            st.session_state.current_input = f"/{prompt}"
                            st.session_state.selected_resource = prompt
                            st.rerun()
                    with col2:
                        st.caption("Prompt")
        
        st.divider()
        
        # Quick Actions
        st.subheader("⚡ Quick Actions")
        if st.button("🔄 Refresh Resources", use_container_width=True):
            with st.spinner("Refreshing..."):
                success, resources, prompts, documents = get_resources()
                if success:
                    st.session_state.resources = resources
                    st.session_state.prompts = prompts
                    st.session_state.documents = documents
                    st.success("Resources refreshed!")
                    st.rerun()
                else:
                    st.error("Failed to refresh resources")
        
        if st.button("📋 List All Resources", use_container_width=True):
            st.session_state.current_input = "list resources"
            st.rerun()
        
        if st.button("❓ Show Help", use_container_width=True):
            st.session_state.current_input = "help"
            st.rerun()

# Main content area
st.title("🤖 MCP Command Interface")
st.markdown("Enhanced interface for MCP server with real-time autocomplete and resource browser")

if not st.session_state.connected:
    st.warning("👈 Please connect to the MCP server using the sidebar")
    st.info("Once connected, you'll see all available resources in the sidebar for easy browsing.")
else:
    # Enhanced command interface
    col1, col2 = st.columns([2, 1])
    
    # Remove text_area_content from session state initialization (around line 35)
    # if 'text_area_content' not in st.session_state:
    #     st.session_state.text_area_content = ""
    
    with col1:
        # In the command input section (around line 310-330), replace:
        with col1:
            st.subheader("💻 Command Input")
            
            # Show selected resource info
            if st.session_state.selected_resource:
                st.info(f"🎯 Selected: {st.session_state.selected_resource}")
            
            # Clean command input without previous outputs
            command_input = st.text_area(
                "Enter your command (type @ for documents, / for prompts):",
                value=st.session_state.current_input,
                height=200,
                placeholder="Type your command here...\nTry typing @ or / to see autocomplete!\nOr click resources in the sidebar!",
                key="command_text_area"
            )
            
            # Update current input
            if command_input != st.session_state.current_input:
                st.session_state.current_input = command_input
                suggestions, suggestion_type = get_real_time_suggestions(command_input)
                st.session_state.current_suggestions = suggestions
                st.session_state.suggestion_type = suggestion_type
                st.session_state.show_suggestions = len(suggestions) > 0
                st.rerun()
    
    with col2:
        st.subheader("💡 Live Suggestions")
        
        if st.session_state.show_suggestions and st.session_state.current_suggestions:
            suggestion_type_icon = "📄" if st.session_state.suggestion_type == "document" else "💬"
            st.write(f"{suggestion_type_icon} **{st.session_state.suggestion_type.title()} Suggestions:**")
            
            for i, suggestion in enumerate(st.session_state.current_suggestions[:8]):
                if st.button(
                    f"{suggestion_type_icon} {suggestion}", 
                    key=f"suggestion_btn_{i}",
                    use_container_width=True
                ):
                    apply_suggestion(suggestion, st.session_state.suggestion_type)
                    st.rerun()
        else:
            st.info("💡 Type @ or / in the command input to see suggestions here!")
            st.markdown("**Or use the sidebar to browse resources**")
    
    # Command execution controls
    st.subheader("🚀 Execute Command")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Execute Command", type="primary", disabled=not st.session_state.current_input.strip()):
            if st.session_state.current_input.strip():
                with st.spinner("Executing..."):
                    output, formatted_result = execute_command(st.session_state.current_input.strip())
                    
                    # Only add to command history, not to text_area_content
                    st.session_state.command_history.append({
                        'command': st.session_state.current_input.strip(),
                        'output': output
                    })
                    
                    st.session_state.current_input = ""
                    st.session_state.show_suggestions = False
                    st.session_state.current_suggestions = []
                    st.session_state.selected_resource = None
                    st.rerun()
    
    with col2:
        if st.button("Clear Input"):
            st.session_state.current_input = ""
            st.session_state.show_suggestions = False
            st.session_state.current_suggestions = []
            st.session_state.selected_resource = None
            st.rerun()
    
    with col3:
        if st.button("Clear History"):
            st.session_state.current_input = ""
            st.session_state.command_history = []
            st.session_state.show_suggestions = False
            st.session_state.current_suggestions = []
            st.session_state.selected_resource = None
            st.rerun()
    
    # Add command history display section after the execute buttons:
    if st.session_state.command_history:
        st.subheader("📜 Command History")
        
        # Create a container with scrollable history
        with st.container(height=400):
            for i, entry in enumerate(reversed(st.session_state.command_history)):
                with st.expander(f"Command {len(st.session_state.command_history) - i}: {entry['command']}", expanded=(i == 0)):
                    st.code(entry['output'], language='text')
                
                if i < len(st.session_state.command_history) - 1:
                    st.divider()
    else:
        st.info("No command history yet. Execute a command to see results here.")

# Instructions
st.header("How to Use Real-time Autocomplete")
st.markdown("""
### 🚀 Real-time Autocomplete Features:
- **@ symbol**: Type `@` and see document suggestions appear instantly on the right
- **/ symbol**: Type `/` and see prompt suggestions appear instantly on the right
- **Live updates**: Suggestions update as you type more characters
- **Click to complete**: Click any suggestion to auto-complete your input
- **Inline output**: Command results appear immediately below the input area

### 💡 Examples:
1. Type `@` → See all documents
2. Type `@dep` → See documents starting with "dep"
3. Type `/` → See all prompts  
4. Type `/sum` → See prompts starting with "sum"
5. Type `Please read @document.md and /analyze it` → Get suggestions for both

### 📝 Steps:
1. **Connect**: Click "Connect to MCP Server" 
2. **Browse**: See available resources, prompts, and documents
3. **Type**: Start typing in the command input
4. **Autocomplete**: Type @ or / to see live suggestions
5. **Select**: Click suggestions to auto-complete
6. **Execute**: Run your command and see results immediately below

### 🎯 Pro Tips:
- **Inline results**: Output appears immediately after execution
- **Real-time suggestions**: No waiting, instant feedback
- **Multiple references**: Use multiple @ and / in the same command
- **Quick actions**: Use buttons for common commands
- **Clear controls**: Clear input or output anytime
""")