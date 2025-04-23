import json
import os
import streamlit as st
from typing import Dict, List, Optional
global library, prompts
# Global variables
library = None
prompts = None

class PromptLibrary:
    def __init__(self, storage_path: str = "prompts.json"):
        self.storage_path = storage_path
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, List[Dict]]:
        """Load prompts from storage file."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        return {"PRD": []}

    def _save_prompts(self) -> None:
        """Save prompts to storage file."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.prompts, f, indent=2)

    def add_prompt(self, name: str, content: str, description: str = "") -> None:
        """Add a new prompt to the library."""
        
        prompt = {
            "name": name,
            "content": content,
            "description": description
        }
        self.prompts["PRD"].append(prompt)
        self._save_prompts()

    def get_prompt(self, name: str) -> Optional[Dict]:
        """Retrieve a prompt by name."""
        for prompt in self.prompts["PRD"]:
            if prompt["name"] == name:
                return prompt
        return None

    def list_prompts(self) -> List[Dict]:
        """List all prompts."""
        return self.prompts["PRD"]

    def delete_prompt(self, name: str) -> bool:
        """Delete a prompt from the library."""
        for i, prompt in enumerate(self.prompts["PRD"]):
            if prompt["name"] == name:
                self.prompts["PRD"].pop(i)
                self._save_prompts()
                return True
        return False

    def clear_all_prompts(self) -> None:
        """Clear all prompts from the library."""
        self.prompts["PRD"] = []
        self._save_prompts()

def initialize_globals():
    """Initialize global variables."""
    global library, prompts
    if library is None:
        library = PromptLibrary()
    if prompts is None:
        prompts = library.list_prompts()

initialize_globals()

# Main container with dark theme styling
st.markdown("""
    <style>
    .main-container {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.write("Creates a minimalistic window for the prompt library.")
# Prompts section with modern styling
st.subheader("📝 Prompts")

# Add button in the top right
col1, col2 = st.columns([6, 1])
with col2:
    if st.button("➕", help="Add new prompt", use_container_width=True):
        st.session_state.show_add = not st.session_state.show_add
        st.session_state.show_edit = False

# Prompt management section
if prompts:
    st.markdown("### Available Prompts ({})".format(len(prompts)))
    
    # Prompt selection with modern styling
    prompt_options = [p["name"] for p in prompts]
    selected_prompt = st.selectbox(
        "",  # Empty label for cleaner look
        options=prompt_options,
        key="select_prompt",
        format_func=lambda x: f"📄 {x}"
    )
    
    if selected_prompt:
        prompt = library.get_prompt(selected_prompt)
        if prompt:
            # Action buttons in a horizontal row
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("✏️", key="edit_btn", help="Edit prompt"):
                    st.session_state.show_edit = not st.session_state.show_edit
            with col2:
                if st.button("🗑️", key="delete_btn", help="Delete prompt"):
                    st.session_state.show_delete = not st.session_state.show_delete
            with col3:
                if st.button("♻️", key="recycle_btn", help="Clear all prompts"):
                    st.session_state.show_clear = not st.session_state.show_clear
            
            # Prompt content display
            st.text_area(
                "Prompt Content",
                value=prompt["content"],
                height=200,
                disabled=True,
                label_visibility="collapsed"
            )

# Add new prompt form
if st.session_state.show_add:
    with st.form("new_prompt_form"):
        st.subheader("Add New Prompt")
        name = st.text_input("Name", key="new_prompt_name")
        content = st.text_area("Content", height=150, key="new_prompt_content")
        description = st.text_input("Description (optional)", key="new_prompt_desc")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("Save", type="primary")
            if submit and name and content:
                library.add_prompt(name, content, description)
                st.session_state.show_add = False
                st.success("✅ Prompt saved")
                st.rerun()
        with col2:
            if st.form_submit_button("Cancel"):
                st.session_state.show_add = False
                st.rerun()

# Confirmation dialogs with proper spacing
if st.session_state.show_delete:
    st.warning("Delete this prompt?")
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Yes", key="confirm_delete", type="primary", use_container_width=True):
            library.delete_prompt(selected_prompt)
            st.session_state.show_delete = False
            st.success("✅")
            st.rerun()
    with col2:
        if st.button("No", key="cancel_delete", type="secondary", use_container_width=True):
            st.session_state.show_delete = False
            st.rerun()
            
    if st.session_state.show_clear:
        st.warning("Clear all prompts?")
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("Yes", key="confirm_clear", type="primary", use_container_width=True):
                library.clear_all_prompts()
                st.session_state.show_clear = False
                st.success("✅")
                st.rerun()
        with col2:
            if st.button("No", key="cancel_clear", type="secondary", use_container_width=True):
                st.session_state.show_clear = False
                st.rerun()
else:
    st.info("No prompts available")
