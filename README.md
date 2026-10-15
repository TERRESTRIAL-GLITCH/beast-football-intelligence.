# BEAST Football Intelligence

## Launch on Streamlit Community Cloud

1. Create a GitHub account at https://github.com/signup
2. Create a public repository named `beast-football-intelligence`.
3. Add `app.py` and `requirements.txt` from this folder to the repository.
4. Open https://share.streamlit.io/ and sign in.
5. Choose **Create app**, select your repository, branch `main`, and file `app.py`, then deploy.

Official guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## Load your existing predictions

In Google Colab run:
```python
out.to_csv("beast_predictions.csv", index=False)
from google.colab import files
files.download("beast_predictions.csv")
```
In the deployed app, open **Upload / Setup** and upload `beast_predictions.csv`.

This loads predictions already produced by your notebook. To make predictions for future fixtures automatically, we must locate the saved fitted model and supply a fixture CSV with the same features the model expects.

## News
The dashboard fetches public RSS headlines from BBC Sport, Sky Sports, ESPN and Google News. Headlines are cached for 15 minutes. Feeds may be unavailable at times.

## Notes
- The app does not directly connect to your Colab runtime.
- Do not upload secrets, API keys, or passwords.
- Model probabilities are estimates, not guarantees.
