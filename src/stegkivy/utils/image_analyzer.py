from PIL import Image
import os
from stegano import lsb
import base64
import zlib
import magic
import exifread
from typing import Dict, Any
import numpy as np
from scipy import stats

class ImageAnalyzer:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.filename = os.path.basename(image_path)
        self.results = {}
        
    def analyze(self) -> Dict[str, Any]:
        self.results = {
            'filename': self.filename,
            'basic_info': self._get_basic_info(),
            'metadata': self._get_metadata(),
            'steganography': self._check_steganography(),
            'compression': self._analyze_compression(),
            'file_type': self._get_file_type(),
            'statistical_analysis': self._perform_statistical_analysis(),
            'potential_methods': self._detect_potential_methods()
        }
        return self.results
    
    def _get_basic_info(self) -> Dict[str, Any]:
        with Image.open(self.image_path) as img:
            return {
                'format': img.format,
                'size': img.size,
                'mode': img.mode,
                'file_size': f"{os.path.getsize(self.image_path) / 1024:.2f} KB",
                'bits_per_channel': img.bits if hasattr(img, 'bits') else 8
            }
    
    def _get_metadata(self) -> Dict[str, Any]:
        """Extract EXIF and other metadata"""
        with open(self.image_path, 'rb') as f:
            tags = exifread.process_file(f)
            return {str(k): str(v) for k, v in tags.items() if not k.startswith('JPEGThumbnail')}
    
    def _perform_statistical_analysis(self) -> Dict[str, Any]:
        with Image.open(self.image_path) as img:
            img_array = np.array(img)
            results = {}
            
            # Analyze least significant bits
            lsb_array = img_array & 1
            lsb_distribution = np.mean(lsb_array)
            
            # Chi-square test for randomness
            observed = np.bincount(lsb_array.flatten())
            expected = len(lsb_array.flatten()) / 2
            chi2, p_value = stats.chisquare([observed[0], observed[1]], 
                                          [expected, expected])
            
            results['lsb_distribution'] = f"{lsb_distribution:.3f}"
            results['chi_square_p_value'] = f"{p_value:.3f}"
            results['randomness_suspicious'] = p_value < 0.05
            
            return results
    
    def _check_steganography(self) -> Dict[str, Any]:
        results = {
            'has_hidden_data': False,
            'confidence': 'Low',
            'detected_methods': []
        }
        
        # Check LSB steganography
        try:
            revealed = lsb.reveal(self.image_path)
            if revealed:
                results['has_hidden_data'] = True
                results['detected_methods'].append('LSB')
                results['confidence'] = 'High'
                
                # Additional checks on revealed data
                if self._is_base64(revealed):
                    results['detected_methods'].append('Base64 Encoding')
                if self._is_compressed(revealed):
                    results['detected_methods'].append('Compression')
                if self._check_7z_signature(revealed):
                    results['detected_methods'].append('7z Container')
        except Exception:
            pass
        
        # Statistical analysis results
        stats = self._perform_statistical_analysis()
        if stats['randomness_suspicious']:
            results['confidence'] = 'Medium'
            results['detected_methods'].append('Statistical Anomalies')
        
        return results
    
    def _analyze_compression(self) -> Dict[str, Any]:
        """Analyze image compression"""
        with Image.open(self.image_path) as img:
            compression_info = {
                'compression': 'none',
                'compression_level': 'unknown',
                'details': []
            }
            
            # Calculate compression ratio first
            file_size = os.path.getsize(self.image_path)
            width, height = img.size
            bits_per_channel = img.bits if hasattr(img, 'bits') else 8
            theoretical_size = width * height * len(img.getbands()) * (bits_per_channel / 8)
            compression_ratio = theoretical_size / file_size
            
            # Check file format specific compression
            if img.format == 'JPEG':
                compression_info['compression'] = 'JPEG DCT'
                try:
                    quality = self._estimate_jpeg_quality(img)
                    compression_info['compression_level'] = f"~{quality}%"
                    compression_info['details'].append(f"JPEG Quality: ~{quality}%")
                except:
                    compression_info['compression_level'] = 'Standard JPEG'
            
            elif img.format == 'PNG':
                # PNG always uses DEFLATE compression
                compression_info['compression'] = 'PNG DEFLATE'
                if 'compress_level' in img.info:
                    compression_info['compression_level'] = str(img.info['compress_level'])
                elif compression_ratio > 8:
                    compression_info['compression_level'] = 'High'
                elif compression_ratio > 4:
                    compression_info['compression_level'] = 'Medium'
                else:
                    compression_info['compression_level'] = 'Low'
            
            # Update compression type based on ratio if not already set
            if compression_info['compression'] == 'none' and compression_ratio > 1.5:
                compression_info['compression'] = 'Generic'
                if compression_ratio > 8:
                    compression_info['compression_level'] = 'High'
                elif compression_ratio > 4:
                    compression_info['compression_level'] = 'Medium'
                else:
                    compression_info['compression_level'] = 'Low'
            
            compression_info['details'].append(f"Compression ratio: {compression_ratio:.2f}:1")
            if compression_ratio > 1.5:
                compression_info['details'].append(
                    f"Space saved: {((1 - (file_size / theoretical_size)) * 100):.1f}%"
                )
            
            return compression_info
    
    def _estimate_jpeg_quality(self, img) -> int:
        """Estimate JPEG quality based on quantization tables"""
        if not hasattr(img, 'quantization'):
            return 0
        
        # Get the first quantization table
        qtables = img.quantization
        if not qtables:
            return 0
        
        # Simple quality estimation based on average quantization values
        # Higher quantization values indicate lower quality
        first_table = qtables[0]
        avg_quantization = sum(first_table) / len(first_table)
        
        # Convert average quantization to quality percentage
        # This is a rough estimation
        quality = max(0, min(100, int(100 - (avg_quantization / 2))))
        return quality
    
    def _get_file_type(self) -> str:
        """Get detailed file type information"""
        return magic.from_file(self.image_path)
    
    def _detect_potential_methods(self) -> list:
        """Detect potential steganography methods used"""
        methods = []
        with Image.open(self.image_path) as img:
            if img.mode in ['RGB', 'RGBA']:
                methods.append('LSB (Least Significant Bit)')
            if 'transparency' in img.info:
                methods.append('Alpha Channel')
            if img.format == 'PNG':
                methods.append('PNG Metadata')
        return methods
    
    def _is_base64(self, s: str) -> bool:
        try:
            return bool(base64.b64decode(s.encode()))
        except Exception:
            return False
    
    def _is_compressed(self, data: str) -> bool:
        try:
            decoded = base64.b64decode(data)
            zlib.decompress(decoded)
            return True
        except Exception:
            return False
    
    def _check_7z_signature(self, data: str) -> bool:
        try:
            decoded = base64.b64decode(data)
            return decoded.startswith(b'7z\xbc\xaf\x27\x1c')
        except Exception:
            return False