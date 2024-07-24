import streamlit as st


def PresenterOutput(Presentation):
    if not isinstance(Presentation, dict) or 'slides' not in Presentation:
        st.error("Invalid presentation data structure")
        st.write("Received data:")
        st.write(Presentation)
        return

    slides = Presentation['slides']

    if not slides:
        st.error("No slides found in the presentation data")
        st.write("Received data:")
        st.write(Presentation)
        return

    if 'current_slide' not in st.session_state:
        st.session_state.current_slide = 0

    # Create two columns with custom widths
    _, col1, col2 = st.columns([0.5,3, 2])

    

    with col1:
        with st.container():
            st.subheader("Presentation")
            presentation_box = st.empty()
    
    with col2:
        with st.container():
            st.subheader("Script")
            script_box = st.empty()

    # Display current slide
    current_slide = slides[st.session_state.current_slide]
    
    with presentation_box.container():
        title = current_slide.get('title', 'No Title').replace("\n", "<br>")
        content = current_slide.get('content', 'No Content').replace("\n", "<br>")
        st.markdown(f"<div style='background-color: #1f2633; padding: 10px; border-radius: 5px; border: 2px solid #3c4861;'>"
                    f"<strong style='font-size: larger;'>{title}<br><br></strong>"
                    f"{content}"
                    f"</div>", unsafe_allow_html=True)
        
        st.write("\n\n")
        prev_col,  next_col, _,  _,_= st.columns([1,1, 1, 1, 1])

        with prev_col:
            if st.button("◀️ Previous"):
                if st.session_state.current_slide > 0:
                    st.session_state.current_slide -= 1
        with next_col:
            if st.button("Next ▶️"):
                if st.session_state.current_slide < len(slides) - 1:
                    st.session_state.current_slide += 1

        # Slide selection
        st.session_state.current_slide = st.select_slider(
            "Select a slide",
            options=range(len(slides)),
            value=st.session_state.current_slide,
            format_func=lambda x: f"Slide {x + 1}"
        )

    with script_box.container():
        st.markdown(f"<div style='background-color: #1f2633; padding: 10px; border-radius: 5px;border: 2px solid #3c4861;text-align: justify;'>"
                    f"{current_slide.get('script', 'No Script')}"
                    f"</div>", unsafe_allow_html=True)

    # Navigation buttons

    if not isinstance(Presentation, dict) or 'slides' not in Presentation:
        st.error("Invalid presentation data structure")
        st.write("Received data:")
        st.write(Presentation)
        return

    slides = Presentation['slides']

    if not slides:
        st.error("No slides found in the presentation data")
        st.write("Received data:")
        st.write(Presentation)
        return

    if 'current_slide' not in st.session_state:
        st.session_state.current_slide = 0

    # Create two columns with custom widths
    col1, col2 = st.columns([3, 2])

    with col1:
        with st.container():
            st.subheader("Presentation")
            presentation_box = st.empty()
    
    with col2:
        with st.container():
            st.subheader("Script")
            script_box = st.empty()

    # Display current slide
    current_slide = slides[st.session_state.current_slide]
    
    with presentation_box.container():
        title = current_slide.get('title', 'No Title').replace("\n", "<br>")
        content = current_slide.get('content', 'No Content').replace("\n", "<br>")
        st.markdown(f"<div style='background-color: #1f2633; padding: 10px; border-radius: 5px; border: 2px solid #3c4861;'>"
                    f"<strong style='font-size: larger;'>{title}<br></strong>"
                    f"{content}"
                    f"</div>", unsafe_allow_html=True)
        
        st.write("\n\n")
        prev_col, _,  _ ,next_col= st.columns([1, 1, 1, 1])

        with prev_col:
            if st.button("◀️ Previous"):
                if st.session_state.current_slide > 0:
                    st.session_state.current_slide -= 1
        with next_col:
            if st.button("Next ▶️"):
                if st.session_state.current_slide < len(slides) - 1:
                    st.session_state.current_slide += 1

        # Slide selection
        st.session_state.current_slide = st.select_slider(
            "Select a slide",
            options=range(len(slides)),
            value=st.session_state.current_slide,
            format_func=lambda x: f"Slide {x + 1}"
        )

    with script_box.container():
        st.markdown(f"<div style='background-color: #1f2633; padding: 10px; border-radius: 5px;border: 2px solid #3c4861;'>"
                    f"{current_slide.get('script', 'No Script')}"
                    f"</div>", unsafe_allow_html=True)

    # Navigation buttons


def main():
    st.set_page_config(layout="wide")
    

    

if __name__ == "__main__":  
    main()