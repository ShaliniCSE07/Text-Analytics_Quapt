import unittest
import json
import sqlite3
import os
from app.emotion import (
    predict_emotion,
    EMOTION_LABEL_MAPPING,
    BUSINESS_EMOTIONS,
    EMOTION_CONFIDENCE_THRESHOLD
)
from app.pipeline import analyze_review


class EmotionAnalysisTest(unittest.TestCase):
    def test_emotion_mapping_and_structure(self):
        """Verify the 6 business emotions are defined with valid source labels."""
        self.assertEqual(len(BUSINESS_EMOTIONS), 6)
        self.assertIn("Anger", BUSINESS_EMOTIONS)
        self.assertIn("Frustration", BUSINESS_EMOTIONS)
        self.assertIn("Disappointment", BUSINESS_EMOTIONS)
        self.assertIn("Anxiety", BUSINESS_EMOTIONS)
        self.assertIn("Confusion", BUSINESS_EMOTIONS)
        self.assertIn("Delight", BUSINESS_EMOTIONS)

        for emo, labels in EMOTION_LABEL_MAPPING.items():
            self.assertIsInstance(labels, list)
            self.assertGreater(len(labels), 0)

    def test_delight_prediction(self):
        """Test representative positive review expressing clear delight."""
        text = "Cashless approval at the hospital came through in under two hours. Really impressed with the team!"
        res = predict_emotion(text)
        self.assertEqual(res["emotion"], "Delight")
        self.assertGreaterEqual(res["confidence"], 50)
        self.assertIn("Delight", res["mapped_scores"])
        self.assertFalse(res["is_uncertain"])

    def test_frustration_and_disappointment(self):
        """Test negative review expressing frustration or disappointment."""
        text = "Customer care kept me on hold for 40 minutes and nobody could answer my simple query, very annoyed."
        res = predict_emotion(text)
        self.assertIn(res["emotion"], ["Frustration", "Anger", "Disappointment"])
        self.assertGreater(res["confidence"], 0)

    def test_anxiety_prediction(self):
        """Test review expressing anxiety/fear regarding claim rejection."""
        text = "I am so terrified and nervous that my surgery claim will be rejected. Very stressful situation."
        res = predict_emotion(text)
        self.assertEqual(res["emotion"], "Anxiety")
        self.assertGreaterEqual(res["confidence"], 40)

    def test_curiosity_without_confusion(self):
        """Curiosity without confusion indicators should not be forced into Confusion."""
        text = "I wonder if you offer zero depreciation for commercial vehicles? Just inquiring."
        res = predict_emotion(text)
        self.assertNotEqual(res["emotion"], "Confusion")

    def test_confusion_with_context(self):
        """Review expressing genuine confusion with indicators."""
        text = "I don't understand why they deducted money without explanation. Very confusing policy clauses."
        res = predict_emotion(text)
        self.assertIn(res["emotion"], ["Confusion", "Frustration", "Disappointment"])

    def test_empty_and_unsupported(self):
        """Test empty string and unsupported language handling in pipeline."""
        empty_res = analyze_review({"Review": ""})
        self.assertEqual(empty_res["Emotion"], "language unsupported")
        self.assertEqual(empty_res["Emotion_Confidence"], 0)

        french_res = analyze_review({"Review": "Ce produit est magnifique mais le service est terrible."})
        self.assertEqual(french_res["Emotion"], "language unsupported")

    def test_sqlite_persistence(self):
        """Verify that SQLite Customer_Reviews_Analysis table has emotion columns."""
        db_path = "data/reviews.db"
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(Customer_Reviews_Analysis)")
                cols = {row[1] for row in cursor.fetchall()}
                self.assertIn("Emotion", cols)
                self.assertIn("Emotion_Confidence", cols)
                self.assertIn("Emotion_Scores", cols)
                self.assertIn("Emotion_Model", cols)


if __name__ == "__main__":
    unittest.main()
