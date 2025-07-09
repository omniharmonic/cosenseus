"""
Core Text Processing Engine
Handles tokenization, cleaning, normalization, and preprocessing of text data
"""

import re
import string
import unicodedata
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize, wordpunct_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
import spacy

# Download required NLTK data on first import
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
    
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

@dataclass
class ProcessingOptions:
    """Configuration options for text processing"""
    remove_punctuation: bool = True
    remove_numbers: bool = False
    remove_stopwords: bool = False
    lowercase: bool = True
    remove_extra_whitespace: bool = True
    remove_urls: bool = True
    remove_emails: bool = True
    remove_html: bool = True
    normalize_unicode: bool = True
    stem_words: bool = False
    lemmatize_words: bool = False
    min_word_length: int = 1
    max_word_length: int = 50
    preserve_sentence_structure: bool = False

class TextProcessor:
    """
    Comprehensive text processing pipeline for civic discourse analysis
    """
    
    def __init__(self):
        """Initialize the text processor with required models"""
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        
        # Try to load spaCy model, fallback if not available
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: spaCy English model not found. Some features may be limited.")
            self.nlp = None
            
        # Common civic discourse terms to preserve
        self.civic_terms = {
            'democracy', 'voting', 'citizen', 'government', 'policy', 'legislation',
            'representative', 'senator', 'congressman', 'mayor', 'governor', 'president',
            'constitution', 'amendment', 'bill', 'law', 'regulation', 'ordinance',
            'budget', 'tax', 'public', 'community', 'municipal', 'federal', 'state',
            'civic', 'political', 'election', 'campaign', 'ballot', 'referendum'
        }
        
        # Load English stopwords
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            self.stop_words = set()
    
    def preprocess(self, text: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main preprocessing pipeline that applies all cleaning and normalization steps
        
        Args:
            text: Input text to process
            options: Processing configuration options
            
        Returns:
            Dictionary containing processed text, tokens, and metadata
        """
        if not text or not isinstance(text, str):
            return {
                "processed_text": "",
                "tokens": [],
                "cleaned_text": "",
                "metadata": {"error": "Invalid input text"}
            }
        
        # Parse options
        opts = ProcessingOptions()
        if options:
            if isinstance(options, dict):
                for key, value in options.items():
                    if hasattr(opts, key):
                        setattr(opts, key, value)
            else:
                # If options is already a ProcessingOptions object
                opts = options
        
        # Track processing steps
        metadata = {
            "original_length": len(text),
            "processing_steps": [],
            "language": "en",  # Default to English, can be enhanced with detection
            "civic_terms_found": []
        }
        
        # Step 1: Initial cleaning
        processed_text = self._initial_clean(text, opts, metadata)
        
        # Step 2: Normalize unicode
        if opts.normalize_unicode:
            processed_text = self._normalize_unicode(processed_text)
            metadata["processing_steps"].append("unicode_normalization")
        
        # Step 3: Remove HTML tags
        if opts.remove_html:
            processed_text = self._remove_html(processed_text)
            metadata["processing_steps"].append("html_removal")
        
        # Step 4: Remove URLs and emails
        if opts.remove_urls:
            processed_text = self._remove_urls(processed_text)
            metadata["processing_steps"].append("url_removal")
            
        if opts.remove_emails:
            processed_text = self._remove_emails(processed_text)
            metadata["processing_steps"].append("email_removal")
        
        # Step 5: Tokenization
        tokens = self.tokenize(processed_text, "words")
        
        # Step 6: Advanced token processing
        if opts.remove_stopwords or opts.stem_words or opts.lemmatize_words:
            tokens = self._process_tokens(tokens, opts, metadata)
            metadata["processing_steps"].append("token_processing")
        
        # Step 7: Filter tokens by length
        if opts.min_word_length > 1 or opts.max_word_length < 50:
            original_count = len(tokens)
            tokens = [
                token for token in tokens 
                if opts.min_word_length <= len(token) <= opts.max_word_length
            ]
            metadata["tokens_filtered"] = original_count - len(tokens)
            metadata["processing_steps"].append("length_filtering")
        
        # Step 8: Detect civic terms
        civic_terms_found = [token.lower() for token in tokens if token.lower() in self.civic_terms]
        metadata["civic_terms_found"] = list(set(civic_terms_found))
        
        # Step 9: Reconstruct text or keep tokens
        if opts.preserve_sentence_structure:
            final_text = self._reconstruct_sentences(tokens)
        else:
            final_text = " ".join(tokens)
        
        # Final cleaning
        cleaned_text = self._final_clean(final_text, opts)
        
        # Update metadata
        metadata.update({
            "final_length": len(cleaned_text),
            "token_count": len(tokens),
            "compression_ratio": len(cleaned_text) / len(text) if len(text) > 0 else 0,
            "processing_complete": True
        })
        
        return {
            "processed_text": final_text,
            "tokens": tokens,
            "cleaned_text": cleaned_text,
            "metadata": metadata
        }
    
    def tokenize(self, text: str, tokenize_by: str = "words") -> List[str]:
        """
        Tokenize text by different units
        
        Args:
            text: Input text
            tokenize_by: Type of tokenization (words, sentences, paragraphs)
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        if tokenize_by == "words":
            return word_tokenize(text)
        elif tokenize_by == "sentences":
            return sent_tokenize(text)
        elif tokenize_by == "paragraphs":
            return [p.strip() for p in text.split('\n\n') if p.strip()]
        elif tokenize_by == "wordpunct":
            return wordpunct_tokenize(text)
        else:
            # Default to word tokenization
            return word_tokenize(text)
    
    def clean_text(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """
        Clean text without full preprocessing
        
        Args:
            text: Input text
            options: Cleaning options
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        opts = ProcessingOptions()
        if options:
            if isinstance(options, dict):
                for key, value in options.items():
                    if hasattr(opts, key):
                        setattr(opts, key, value)
            else:
                opts = options
        
        cleaned = text
        
        if opts.remove_html:
            cleaned = self._remove_html(cleaned)
        
        if opts.remove_urls:
            cleaned = self._remove_urls(cleaned)
        
        if opts.remove_emails:
            cleaned = self._remove_emails(cleaned)
        
        if opts.remove_extra_whitespace:
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        if opts.lowercase:
            cleaned = cleaned.lower()
        
        if opts.remove_punctuation:
            cleaned = cleaned.translate(str.maketrans('', '', string.punctuation))
        
        return cleaned
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent processing
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        if not text:
            return ""
        
        # Unicode normalization
        normalized = unicodedata.normalize('NFKD', text)
        
        # Convert to ASCII, removing accents
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Basic cleaning
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _initial_clean(self, text: str, opts: ProcessingOptions, metadata: Dict) -> str:
        """Initial text cleaning operations"""
        cleaned = text.strip()
        
        if opts.remove_extra_whitespace:
            cleaned = re.sub(r'\s+', ' ', cleaned)
            metadata["processing_steps"].append("whitespace_normalization")
        
        return cleaned
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters"""
        return unicodedata.normalize('NFKD', text)
    
    def _remove_html(self, text: str) -> str:
        """Remove HTML tags"""
        html_pattern = re.compile(r'<[^>]+>')
        return html_pattern.sub('', text)
    
    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        return url_pattern.sub('', text)
    
    def _remove_emails(self, text: str) -> str:
        """Remove email addresses"""
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        return email_pattern.sub('', text)
    
    def _process_tokens(self, tokens: List[str], opts: ProcessingOptions, metadata: Dict) -> List[str]:
        """Process individual tokens based on options"""
        processed_tokens = []
        
        for token in tokens:
            # Skip empty tokens
            if not token.strip():
                continue
            
            # Convert to lowercase if requested
            if opts.lowercase:
                token = token.lower()
            
            # Remove punctuation if requested
            if opts.remove_punctuation:
                token = token.translate(str.maketrans('', '', string.punctuation))
                if not token:  # Skip if token becomes empty
                    continue
            
            # Remove numbers if requested
            if opts.remove_numbers and token.isdigit():
                continue
            
            # Remove stopwords if requested (but preserve civic terms)
            if opts.remove_stopwords and token.lower() in self.stop_words:
                if token.lower() not in self.civic_terms:
                    continue
            
            # Stem words if requested
            if opts.stem_words:
                token = self.stemmer.stem(token)
            
            # Lemmatize words if requested
            if opts.lemmatize_words:
                token = self.lemmatizer.lemmatize(token)
            
            processed_tokens.append(token)
        
        return processed_tokens
    
    def _reconstruct_sentences(self, tokens: List[str]) -> str:
        """Reconstruct sentences maintaining structure"""
        # Simple reconstruction - can be enhanced with more sophisticated logic
        return " ".join(tokens)
    
    def _final_clean(self, text: str, opts: ProcessingOptions) -> str:
        """Final cleaning operations"""
        if opts.remove_extra_whitespace:
            text = re.sub(r'\s+', ' ', text).strip()
        
        return text 