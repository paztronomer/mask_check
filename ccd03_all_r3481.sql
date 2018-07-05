SET ECHO OFF NEWP 0 SPA 1 PAGES 0 FEED OFF HEAD OFF TRIMS ON LINESIZE 1000
spool ccd03_allY5A1_r3481.txt

select fai.path, fai.filename from file_archive_info fai, desfile d, proctag tag where tag.tag='Y5A1_FINALCUT_TEST_2' and tag.pfw_attempt_id=d.pfw_attempt_id and d.filetype='red_immask' and fai.desfile_id=d.id and fai.filename like '%_c03_%';

exit
