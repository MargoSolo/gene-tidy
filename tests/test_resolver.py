import pytest

from gene_tidy.resolver import resolve_value


def test_approved_symbol(hgnc):
    r = resolve_value("TP53", hgnc)
    assert r.match_status == "matched"
    assert r.approved_symbol == "TP53"
    assert r.hgnc_id == "HGNC:11998"
    assert r.ensembl_gene_id == "ENSG00000141510"
    assert r.uniprot_id == "P04637"
    assert r.entrez_id == "7157"
    assert r.source_used == "hgnc_approved_symbol"
    assert r.manual_review_required is False
    assert r.bucket == "clean"


def test_case_and_whitespace_insensitive(hgnc):
    for v in ["tp53", "  TP53 ", "Tp53"]:
        r = resolve_value(v, hgnc)
        assert r.approved_symbol == "TP53"
        assert r.match_status == "matched"


def test_alias_resolution(hgnc):
    r = resolve_value("p53", hgnc)
    assert r.approved_symbol == "TP53"
    assert r.match_status == "matched_alias"
    assert "alias" in r.warning.lower()
    assert r.bucket == "clean"


def test_prev_symbol_resolution(hgnc):
    r = resolve_value("FRAP1", hgnc)
    assert r.approved_symbol == "MTOR"
    assert r.match_status == "matched_prev"
    assert "previous symbol" in r.warning.lower()


def test_ensembl_gene(hgnc):
    r = resolve_value("ENSG00000141510", hgnc)
    assert r.approved_symbol == "TP53"
    assert r.detected_type == "ensembl_gene"
    assert r.source_used == "hgnc_ensembl_gene_id"


def test_ensembl_gene_with_version_suffix(hgnc):
    r = resolve_value("ENSG00000141510.17", hgnc)
    assert r.approved_symbol == "TP53"


def test_uniprot(hgnc):
    r = resolve_value("P38398", hgnc)
    assert r.approved_symbol == "BRCA1"
    assert r.detected_type == "uniprot"


def test_entrez(hgnc):
    r = resolve_value("672", hgnc)
    assert r.approved_symbol == "BRCA1"
    assert r.detected_type == "entrez"


def test_refseq(hgnc):
    r = resolve_value("NM_000546", hgnc)
    assert r.approved_symbol == "TP53"
    assert r.detected_type == "refseq"


def test_hgnc_id(hgnc):
    r = resolve_value("HGNC:11998", hgnc)
    assert r.approved_symbol == "TP53"
    assert r.detected_type == "hgnc_id"


def test_excel_corruption_unambiguous_recovery(hgnc):
    r = resolve_value("2-Sep", hgnc)
    assert r.match_status == "recovered_excel"
    assert r.approved_symbol == "SEPTIN2"
    assert r.detected_type == "excel_corrupted"
    assert "Excel date-corruption" in r.warning
    assert r.bucket == "clean"


def test_excel_corruption_ambiguous(hgnc):
    r = resolve_value("1-Mar", hgnc)
    assert r.match_status == "ambiguous"
    assert r.manual_review_required is True
    assert set(r.approved_symbol.split(";")) == {"MARCHF1", "MTARC1"}
    assert r.bucket == "ambiguous"


def test_alias_prev_collision_is_ambiguous(hgnc):
    # DEC1 is a previous symbol of DELEC1 AND an alias of BHLHE40.
    r = resolve_value("DEC1", hgnc)
    assert r.match_status == "ambiguous"
    assert set(r.approved_symbol.split(";")) == {"BHLHE40", "DELEC1"}


def test_unmatched(hgnc):
    r = resolve_value("FOOBAR1", hgnc)
    assert r.match_status == "unmatched"
    assert r.bucket == "failed"
    assert r.manual_review_required is True


def test_empty(hgnc):
    r = resolve_value("", hgnc)
    assert r.match_status == "empty"
    assert r.bucket == "failed"
    assert r.manual_review_required is False


def test_transcript_not_resolvable_offline(hgnc):
    r = resolve_value("ENST00000269305", hgnc)
    assert r.detected_type == "ensembl_transcript"
    assert r.match_status == "unmatched"
    assert "transcript" in r.warning.lower()


def test_septin_renamed_symbol_resolves(hgnc):
    # Modern approved symbol resolves directly.
    r = resolve_value("SEPTIN2", hgnc)
    assert r.match_status == "matched"
    assert r.approved_symbol == "SEPTIN2"
    # Legacy SEPT2 resolves via previous symbol.
    r2 = resolve_value("SEPT2", hgnc)
    assert r2.approved_symbol == "SEPTIN2"
    assert r2.match_status == "matched_prev"
