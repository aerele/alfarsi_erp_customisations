from frappe.core.doctype.document_naming_rule.document_naming_rule import (
    DocumentNamingRule,
)


class CustomDocumentNamingRule(DocumentNamingRule):
    def apply(self, doc):
        """
        Skip Document Naming Rule if document
        is created from Lexer Import.
        Applies to ALL doctypes (PO, PI, PR, SO, SI, DN).
        """

        if (
            doc.get("custom_lexer_doc")
            or doc.get("custom_lexer_link_pr")
            or doc.get("custom_lexer_link_in_pi")
            or doc.get("custom_lexer_link_in_so")
            or doc.get("custom_lexer_link_in_dn")
            or doc.get("custom_lexer_in_si")
        ):
            return

        super().apply(doc)
