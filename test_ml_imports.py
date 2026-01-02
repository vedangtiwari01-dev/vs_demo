"""
Quick test to verify ML modules are importable and can be initialized.
Run this before testing with real data.
"""

import sys
import os

# Add the ai-service app to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai-service'))

def test_ml_imports():
    """Test that all ML modules can be imported."""
    print("=" * 60)
    print("Testing ML Module Imports")
    print("=" * 60)

    try:
        print("\n1. Testing FeatureEngineer import...")
        from app.services.ml.feature_engineer import FeatureEngineer
        engineer = FeatureEngineer()
        print("   ✅ FeatureEngineer imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ FeatureEngineer failed: {e}")
        return False

    try:
        print("\n2. Testing DeviationClusterer import...")
        from app.services.ml.clustering import DeviationClusterer
        clusterer = DeviationClusterer()
        print("   ✅ DeviationClusterer imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ DeviationClusterer failed: {e}")
        return False

    try:
        print("\n3. Testing AnomalyDetector import...")
        from app.services.ml.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector(contamination=0.1)
        print("   ✅ AnomalyDetector imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ AnomalyDetector failed: {e}")
        return False

    try:
        print("\n4. Testing IntelligentSampler import...")
        from app.services.ml.intelligent_sampler import IntelligentSampler
        sampler = IntelligentSampler(target_sample_size=75)
        print("   ✅ IntelligentSampler imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ IntelligentSampler failed: {e}")
        return False

    try:
        print("\n5. Testing MLPipeline import...")
        from app.services.ml.ml_pipeline import MLPipeline
        pipeline = MLPipeline(target_sample_size=75, contamination=0.1)
        print("   ✅ MLPipeline imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ MLPipeline failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ All ML modules imported successfully!")
    print("=" * 60)

    # Check dependencies
    print("\n6. Checking ML dependencies...")
    try:
        import sklearn
        print(f"   ✅ scikit-learn version: {sklearn.__version__}")
    except ImportError:
        print("   ❌ scikit-learn not installed. Run: pip install scikit-learn>=1.3.0")
        return False

    try:
        import numpy
        print(f"   ✅ numpy version: {numpy.__version__}")
    except ImportError:
        print("   ❌ numpy not installed. Run: pip install numpy>=1.24.0")
        return False

    print("\n" + "=" * 60)
    print("✅ All dependencies installed correctly!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Restart AI service: cd ai-service && python -m uvicorn main:app --reload")
    print("  2. Test with real data: python test_phase1_real_data.py")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        success = test_ml_imports()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
