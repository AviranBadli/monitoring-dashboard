import streamlit as st


def confirm_delete(item_type: str, item_name: str, key: str) -> bool:
    if st.button("Delete", key=f"del_{key}", type="secondary"):
        st.session_state[f"confirm_{key}"] = True

    if st.session_state.get(f"confirm_{key}"):
        st.warning(f"Delete {item_type} **{item_name}**?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm", key=f"confirm_yes_{key}", type="primary"):
                st.session_state.pop(f"confirm_{key}", None)
                return True
        with col2:
            if st.button("Cancel", key=f"confirm_no_{key}"):
                st.session_state.pop(f"confirm_{key}", None)
                st.rerun()
    return False
