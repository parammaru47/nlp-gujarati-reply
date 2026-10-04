# Gujarati Smart Reply System - Architecture Overview

## Project Overview
The objective was to build a robust, deterministic Gujarati Smart Reply system constrained strictly to CPU-bound classical natural language processing constructs (TF-IDF, LinearSVC, FastText), deliberately avoiding modern Large Language Models (LLMs).

## Architecture and Implementation
The system was built on a two-stage decoupled pipeline. Stage 1 utilized a Dialogue Act Classifier to categorize incoming text into seven functional speech acts (e.g., BINARY_QUESTION, MILESTONE_NEWS, OPEN_INQUIRY). Stage 2 employed a Policy-Constrained Retrieval engine to map the classified intent to exactly three contextually safe, deterministic outgoing response slots. The backend operated as a stateless Flask REST API, interacting asynchronously with a Manifest V3 browser extension. The extension utilized a MutationObserver for dynamic DOM injection targeting WhatsApp Web, successfully bypassing React-controlled virtual DOM event listeners to render clickable Gujarati response chips natively.

## Data and Feature Engineering
To process a massive 13GB/8-million-line IndicNLPv2 Gujarati corpus without triggering out-of-memory errors on a CPU, a lazy-loading Python generator was implemented to stream text into Gensim’s FastText model. The core classification pipeline utilized a customized FeatureUnion that combined dense semantic mean-pooling (300D FastText vectors) with sparse morphological subwords (TF-IDF character n-grams) to capture both deep semantic meaning and explicit Gujarati grammatical suffixes. Extreme class imbalance between intents was mathematically neutralized using algorithmic class weighting (`class_weight="balanced"`) and explicit feature-weight scaling, preventing the dense vectors from washing out smaller, sparse intent classes.

## Technical Successes
The backend flawlessly handled intent classification and utilized a calibrated Out-Of-Domain (OOD) gatekeeper (threshold tuning) to safely trap non-conversational gibberish, routing it to safe deflections rather than hallucinating an intent. The system successfully executed inference in milliseconds on edge hardware.

## Core Learnings and Architectural Limitations
The project successfully mapped the absolute functional ceiling of classical NLP. While the LinearSVC architecture proved highly accurate at isolating and classifying the intent of a message, it natively lacked the ability to process conversational pragmatics and tone. Because classical models route inputs to broad semantic buckets, the deterministic retrieval engine struggled with tonal collisions—such as offering a condolence template in response to a polite goodbye, or attempting to schedule a meeting in response to a milestone celebration.

## Codebase Structure
- **`nlp/api.py`**: The stateless Flask REST backend. Serves exactly constraints, embeds the `MeanFastTextTransformer` definition directly to circumvent namespace unpickling errors, and orchestrates the Out-Of-Domain Gatekeeper rules. 
- **`nlp/train_classifier.py`**: The training harness for generating the Scikit-Learn `FeatureUnion`. Compiles continuous FastText pooling algorithms with sparse `TfidfVectorizer` character morphology algorithms into the balanced `CalibratedClassifierCV(LinearSVC)`.
- **`nlp/train_fasttext_capped.py`**: The semantic generator script. Implements an `itertools.islice` memory-stream class (`GujaratiCorpusStreamer`) to iteratively process exactly 8-million lines of the 13GB corpus without exhausting standard CPU limits.
- **`data/reply_bank.json`**: The ultra-granular policy behavior map. Isolates incoming dialogue intents into precise tonal constraints (e.g. tracking `401 Task Affirmation` tightly away from `402 Policy Agreement`).
- **`data/dialogue_acts.csv`**: The primary tabular training data linking natural language Gujarati variations to the 7 coarse behavioral intents.
- **`data/dialogue_act_model_dense.joblib` & `data/gu_fasttext_lite.model`**: The compiled pipeline artifact caches containing calibrated classifier boundaries and the derived semantic 100D/300D spatial weights.
- **`extension/content.js`**: The asynchronous Chrome Manifest V3 hook. Actively watches the virtual WhatsApp Web DOM using a `MutationObserver`, parses text outputs without breaking React rendering states, and forcibly dispatches ClipboardEvents to insert smart replies.
- **`extension/background.js`**: The service-worker proxy. Bypasses the browser's aggressive Cross-Origin (CORS) restraints by tunneling fetches directly to the local Flask background task.
- **`extension/manifest.json` & `extension/styles.css`**: Extension constraints defining Host Permissions for the localhost port, and UI styling natively skinning the action rack against WhatsApp Web's dark-mode footprints.

## Deployment Guide (Running on a New Machine)
Since the system is deliberately designed to be stateless and localized, deploying it to a new machine requires no external databases or cloud API keys.

1. **Install Dependencies**:
   Ensure Python 3.8+ is installed. Then, install the required classical ML packages:
   ```bash
   pip install flask flask-cors scikit-learn gensim pandas numpy joblib
   ```
2. **Boot the NLP Backend**:
   Navigate to the project root and start the Flask API. This will load the dense FastText matrices into memory and expose the local port:
   ```bash
   python nlp/api.py
   ```
   *(The terminal should output `* Running on http://127.0.0.1:5000`)*
3. **Inject the Extension**:
   - Open Google Chrome and navigate to `chrome://extensions/`.
   - Enable **Developer mode** in the top right corner.
   - Click **Load unpacked** and select the local `extension/` folder.
4. **Initiate the Workflow**:
   Open WhatsApp Web. The extension's `content.js` script will immediately attach to the virtual DOM. Any incoming Gujarati messages will transparently ping `localhost:5000` and natively render the 3 precise smart reply options directly above your chat input.

## Conclusion
Fixing tonal mismatches in classical classification models requires granular, manually mapped sub-class IDs and rigid rule-based heuristics, which effectively degrades the machine learning pipeline into a hardcoded switch statement. This project successfully demonstrated that while classical NLP is highly efficient for isolated text classification, the lack of sequential attention mechanisms makes it fundamentally incapable of safe, dynamic dialogue generation. This limitation perfectly highlights the exact operational gap that prompted the industry shift toward modern, attention-based transformer architectures (LLMs).
