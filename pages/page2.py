import json
import os
import streamlit as st
from typing import Dict, List, Optional

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

"""Creates a minimalistic window for the prompt library."""
global library, prompts
    
initialize_globals()
prompt_window = st.sidebar.container()
with prompt_window:
        # Initialize prompt library and states
        if 'show_add' not in st.session_state:
            st.session_state.show_add = False
        if 'show_edit' not in st.session_state:
            st.session_state.show_edit = False
        if 'show_delete' not in st.session_state:
            st.session_state.show_delete = False
        if 'show_clear' not in st.session_state:
            st.session_state.show_clear = False
        
        # Header with Add button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📚 Prompts")
        with col2:
            if st.button("➕", help="Add new prompt", use_container_width=True):
                st.session_state.show_add = not st.session_state.show_add
                st.session_state.show_edit = False
        
        # Add new prompt
        if st.session_state.show_add:
            with st.container():
                name = st.text_input("Name", key="new_prompt_name")
                content = st.text_area("Content", height=100, key="new_prompt_content")
                description = st.text_input("Description (optional)", key="new_prompt_desc")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("💾", help="Save prompt", use_container_width=True):
                        if name and content:
                            library.add_prompt(name, content, description)
                            st.session_state.show_add = False
                            st.success("✅")
                            st.rerun()
                        else:
                            st.error("❌")
        
        # List and manage prompts
        if prompts:
            st.divider()
            with st.container():
                num_prompts = len(prompts)
                prompt_options = [p["name"] for p in prompts]
                selected_prompt = st.selectbox(
                    f"Available Prompts ({num_prompts})",
                    options=prompt_options,
                    key="select_prompt",
                    format_func=lambda x: f"📄 {x}",
                    help="Select a prompt to view, edit, or use"
                )
                
                if selected_prompt:
                    prompt = library.get_prompt(selected_prompt)
                    if prompt:
                        # Action buttons in a compact row
                        col1, col2, col3 = st.columns([1,1,1])
                        with col1:
                            if st.button("✏️", help="Edit prompt", key="edit_btn", use_container_width=True):
                                st.session_state.show_edit = not st.session_state.show_edit
                                st.session_state.show_add = False
                        with col2:
                            if st.button("🗑️", help="Delete prompt", key="delete_btn", use_container_width=True):
                                st.session_state.show_delete = not st.session_state.show_delete
                        with col3:
                            if st.button("♻️", help="Clear all prompts", key="clear_btn", use_container_width=True):
                                st.session_state.show_clear = not st.session_state.show_clear
                        
                        # Content display/edit area
                        with st.container():
                            if st.session_state.get('show_edit', False):
                                new_content = st.text_area("Edit Content", prompt["content"], height=100)
                                new_description = st.text_input("Edit Description", prompt["description"])
                                col1, col2 = st.columns([1,1])
                                with col1:
                                    if st.button("Save", key="save_edit", use_container_width=True):
                                        library.delete_prompt(selected_prompt)
                                        library.add_prompt(selected_prompt, new_content, new_description)
                                        st.session_state.show_edit = False
                                        st.success("✅")
                                        st.rerun()
                                with col2:
                                    if st.button("Cancel", key="cancel_edit", use_container_width=True):
                                        st.session_state.show_edit = False
                                        st.rerun()
                            else:
                                st.text_area("Prompt Content", prompt["content"], height=100, disabled=True, label_visibility="collapsed")
                                if prompt["description"]:
                                    st.caption(prompt["description"])
                        
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
                        
                        # Use prompt button
                        if not any([st.session_state.show_edit, st.session_state.show_delete, st.session_state.show_clear]):
                            if st.button("Use Prompt", key="use_prompt", type="primary", use_container_width=True):
                                return prompt["content"]
        else:
            st.info("No prompts available")
