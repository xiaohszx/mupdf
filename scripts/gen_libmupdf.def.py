#!/usr/bin/env python

"""
Generates a list of all exports from libmupdf.dll from the function lists
contained in the mupdf/include/* headers (only MuPDF and MuXPS are included)
and adds exports for the other libraries contained within libmupdf.dll but
used by SumatraPDF-no-MuPDF.exe (unarr, libdjvu, zlib, lzma, libwebp).
"""

import os, re, util

def generateExports(header, exclude=[]):
	if os.path.isdir(header):
		return "\n".join([generateExports(os.path.join(header, file), exclude) for file in os.listdir(header)])

	data = open(header, "r").read()
	data = re.sub(r"(?sm)^#ifndef NDEBUG\s.*?^#endif", "", data, 0)
	data = re.sub(r"(?sm)^#ifdef ARCH_ARM\s.*?^#endif", "", data, 0)
	data = re.sub(r"(?sm)^#ifdef FITZ_DEBUG_LOCKING\s.*?^#endif", "", data, 0)
	data = data.replace(" FZ_NORETURN;", ";")
	functions = re.findall(r"(?sm)^\w+ (?:\w+ )?\*?(\w+)\(.*?\);", data)
	return "\n".join(["\t" + name for name in functions if name not in exclude])

def collectFunctions(file):
	data = open(file, "r").read()
	return re.findall(r"(?sm)^\w+(?: \*\n|\n| \*| )((?:fz_|pdf_|xps_)\w+)\(", data)

LIBMUPDF_DEF = """\
; This file is auto-generated by gen_libmupdf.def.py

LIBRARY MuPDFLib
EXPORTS

; Fitz exports

%(fitz_exports)s

; MuPDF exports

%(mupdf_exports)s

"""

def main():
	util.chdir_top()

	# don't include/export doc_* functions, support for additional input/output formats and form support
	doc_exports = collectFunctions("source/fitz/document-all.c") + ["fz_get_annot_type"]
	more_formats = collectFunctions("source/fitz/svg-device.c") + collectFunctions("source/fitz/output-pcl.c") + collectFunctions("source/fitz/output-pwg.c")
	form_exports = collectFunctions("source/pdf/pdf-form.c") + collectFunctions("source/pdf/pdf-event.c") + collectFunctions("source/pdf/pdf-appearance.c") + ["pdf_access_submit_event", "pdf_init_ui_pointer_event"]
	misc_exports = collectFunctions("source/fitz/stream-prog.c") + collectFunctions("source/fitz/test-device.c") + ["fz_android_fprintf", "fz_getoptw", "fz_valgrind_pixmap", "msvc_snprintf", "msvc_vsnprintf", "track_usage"]
	sign_exports = ["pdf_crypt_buffer", "pdf_read_pfx", "pdf_sign_signature", "pdf_signer_designated_name", "pdf_free_designated_name"]

	fitz_exports = generateExports("include/mupdf/fitz", doc_exports + more_formats + misc_exports)
	mupdf_exports = generateExports("include/mupdf/pdf", form_exports + sign_exports + ["pdf_drop_designated_name", "pdf_print_xref", "pdf_recognize", "pdf_resolve_obj", "pdf_open_compressed_stream"])

	list = LIBMUPDF_DEF % locals()
	open("platform/win32/libmupdf.def", "wb").write(list.replace("\n", "\r\n"))

if __name__ == "__main__":
	main()
