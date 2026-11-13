# Sources

Only official AWS documents are indexed. The raw files are not committed. Download them from the links below and use them for this personal, non-commercial project only; check each document's current terms on the AWS site.

| doc_id | Title | Pages | Downloaded | URL |
|---|---|---|---|---|
| aws-overview | Overview of Amazon Web Services (AWS Whitepaper) | 162 | 2026-11-10 | https://docs.aws.amazon.com/whitepapers/latest/aws-overview/introduction.html |
| generative-ai-lens | Generative AI Lens, AWS Well-Architected Framework | 261 | 2026-11-10 | https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/generative-ai-lens.html |
| aws-kms-best-practices | AWS Key Management Service Best Practices (ARCHIVED, 2021) | 22 | 2021 PDF | https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html (current replacement) |
| aws-security-best-practices | AWS Security Best Practices (ARCHIVED notice only) | 4 | 2026-11-10 | https://docs.aws.amazon.com/whitepapers/latest/aws-security-best-practices/welcome.html |

Notes:

- The KMS paper is marked ARCHIVED by AWS; its cover page points to the developer guide for current guidance. Answers drawn from it can be out of date.
- The Security Best Practices whitepaper has been archived by AWS and now contains little more than the archive notice pointing to newer guidance, so it adds almost no content to the index.
- Downloaded dates are the PDF creation dates; change them if you downloaded on a different day.
- Removed from the index: `kms-cryptographic-details` (the PDF-to-markdown conversion produced garbled text; deleted with `scripts/delete_doc.py`).
- Conversion: PDF to markdown with `pymupdf4llm` (version below 2), keeping headings for structure-aware chunking.
