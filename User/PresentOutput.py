import streamlit as st
import json

# Load the JSON data



if 'step' not in st.session_state:
    st.session_state.step = 1

# Function to move to the next step
def next_step():
    st.session_state.step += 1

def PresenterOutput(Presentation):
    
    #raw_data = json.load(Presentation)
    data = json.loads(Presentation)
    
    
    slides = data['slides']

    if 'current_slide' not in st.session_state:
        st.session_state.current_slide = 0

    # Display current slide
    current_slide = slides[st.session_state.current_slide]
    st.header(current_slide['title'])
    st.write(current_slide['content'])

    # Navigation buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button("◀️ Previous", on_click=next_step):
            if st.session_state.current_slide > 0:
                st.session_state.current_slide -= 1
    with col2:
        if st.button("Next ▶️", on_click=next_step):
            if st.session_state.current_slide < len(slides) - 1:
                st.session_state.current_slide += 1

    
    # Slide selection
    st.session_state.current_slide = st.select_slider(
        "Select a slide",
        options=range(len(slides)),
        value=st.session_state.current_slide,
        format_func=lambda x: f"Slide {x + 1}"
    )


def main():

    st.title("Presentator")



if __name__ == "__main__":
    main()