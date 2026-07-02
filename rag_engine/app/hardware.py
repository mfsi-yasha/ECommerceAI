import logging

logger = logging.getLogger(__name__)


def get_device() -> str:
    """
    Detect and return the best available PyTorch device string.

    Returns:
        'cuda'  — if an NVIDIA GPU is available (requires nvidia-container-toolkit in Docker)
        'mps'   — if running natively on Apple Silicon macOS
        'cpu'   — fallback for all other environments
    """
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"🟢 Hardware detected: NVIDIA CUDA — {gpu_name}")
            return "cuda"

        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            logger.info("🟢 Hardware detected: Apple Silicon MPS")
            return "mps"

        logger.info("🟡 Hardware detected: CPU (fallback)")
        return "cpu"

    except ImportError:
        logger.warning("PyTorch not installed — defaulting to CPU")
        return "cpu"
