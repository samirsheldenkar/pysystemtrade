import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Constants
DATA_PATH = "/home/samir/data"

st.set_page_config(layout="wide", page_title="Futures Data Dashboard")


def get_folders(base_path):
    """Get list of folders in the base path."""
    if not os.path.exists(base_path):
        return []
    return [
        f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))
    ]


def get_subfolders(folder_path):
    """Get list of subfolders in a specific folder."""
    if not os.path.exists(folder_path):
        return []
    return [
        f
        for f in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, f))
    ]


def get_files(folder_path):
    """Get list of files in a folder."""
    if not os.path.exists(folder_path):
        return []
    return [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]


def load_data(file_path):
    """Load data from parquet or csv file."""
    if not os.path.exists(file_path):
        st.error(f"File not found: {file_path}")
        return None

    try:
        # Pysystemtrade parquet files often have index
        if file_path.endswith(".parquet"):
            try:
                df = pd.read_parquet(file_path)
            except ImportError:
                # Fallback if fastparquet/pyarrow issues
                st.error(
                    "Error reading parquet. Ensure pyarrow or fastparquet is installed."
                )
                return None
        elif file_path.endswith(".csv"):
            df = pd.read_csv(file_path, index_col=0, parse_dates=True)
        else:
            return None
        return df
    except Exception as e:
        st.error(f"Error loading {file_path}: {e}")
        return None


def main():
    st.title("Futures Data Dashboard")

    # Sidebar
    st.sidebar.header("Data Selection")

    if not os.path.exists(DATA_PATH):
        st.error(f"Data path {DATA_PATH} does not exist.")
        return

    available_folders = sorted(get_folders(DATA_PATH))

    if not available_folders:
        st.error(f"No folders found in {DATA_PATH}")
        return

    # Use session state to remember selections if possible, but simple selectbox is fine
    ref_idx = 0
    comp_idx = 1 if len(available_folders) > 1 else 0

    ref_folder = st.sidebar.selectbox(
        "Reference Folder", available_folders, index=ref_idx, key="ref_folder"
    )
    comp_folder = st.sidebar.selectbox(
        "Comparison Folder", available_folders, index=comp_idx, key="comp_folder"
    )

    ref_path = os.path.join(DATA_PATH, ref_folder)
    comp_path = os.path.join(DATA_PATH, comp_folder)

    # Subfolders
    ref_subfolders = sorted(get_subfolders(ref_path))

    if not ref_subfolders:
        st.warning(f"No subfolders found in {ref_folder}")
        return

    subfolder = st.sidebar.selectbox("Sub-folder (Category)", ref_subfolders)

    # Files
    ref_sub_path = os.path.join(ref_path, subfolder)
    comp_sub_path = os.path.join(comp_path, subfolder)

    files = sorted(get_files(ref_sub_path))

    if not files:
        st.warning(f"No files found in {ref_folder}/{subfolder}")
        return

    selected_file = st.sidebar.selectbox("Select File", files)

    # Main Content
    st.subheader(f"Analyzing: {selected_file}")

    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Reference: {ref_folder}")
    with col2:
        st.info(f"Comparison: {comp_folder}")

    # Load Data
    ref_file_path = os.path.join(ref_sub_path, selected_file)
    comp_file_path = os.path.join(comp_path, subfolder, selected_file)

    with st.spinner("Loading data..."):
        df_ref = load_data(ref_file_path)
        df_comp = load_data(comp_file_path)

    # Display Reference
    if df_ref is not None:
        st.write(f"### {ref_folder}/{subfolder}/{selected_file}")
        st.dataframe(df_ref.head())

        # Plotting
        # Auto-detect numeric columns for plotting
        numeric_cols = df_ref.select_dtypes(include=["number"]).columns.tolist()

        if numeric_cols:
            selected_col = st.selectbox("Select Column to Plot", numeric_cols)

            fig = px.line(df_ref, y=selected_col, title=f"Reference: {selected_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No numeric columns found for plotting.")

    # Comparison
    if df_comp is not None:
        st.write(f"### {comp_folder}/{subfolder}/{selected_file}")
        # If we want to overlay, we need to inspect the data structure slightly more.
        # Assuming matching indices.

        if df_ref is not None and not df_ref.empty and not df_comp.empty:
            # Comparison Logic
            st.markdown("---")
            st.header("Comparison")

            common_cols = [c for c in df_ref.columns if c in df_comp.columns]
            if common_cols:
                # diff
                try:
                    # Align on index
                    df_ref_aligned, df_comp_aligned = df_ref.align(
                        df_comp, join="inner"
                    )

                    if not df_ref_aligned.empty:
                        diff = (
                            df_ref_aligned[common_cols] - df_comp_aligned[common_cols]
                        )

                        st.subheader("Differences (Ref - Comp)")
                        st.dataframe(diff.describe())

                        diff_col = st.selectbox(
                            "Select Column for Difference Plot",
                            common_cols,
                            key="diff_col",
                        )
                        fig_diff = px.line(
                            diff, y=diff_col, title=f"Difference: {diff_col}"
                        )
                        st.plotly_chart(fig_diff, use_container_width=True)

                        # Combined Plot
                        st.subheader("Overlay Plot")
                        combined = pd.DataFrame(
                            {
                                f"{ref_folder}": df_ref_aligned[diff_col],
                                f"{comp_folder}": df_comp_aligned[diff_col],
                            }
                        )
                        fig_overlay = px.line(combined, title=f"Overlay: {diff_col}")
                        st.plotly_chart(fig_overlay, use_container_width=True)

                    else:
                        st.warning("No overlapping indices found.")
                except Exception as e:
                    st.error(f"Comparison error: {e}")

    else:
        st.warning(
            f"File {selected_file} not found or could not be loaded in {comp_folder}"
        )


if __name__ == "__main__":
    main()
