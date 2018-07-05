select distinct(fai.path), fai.filename 
    from file_archive_info fai, desfile d, proctag tag, pfw_attempt att, 
    gruendl.my_lightbulb6 lb 
    where tag.tag='Y5A1_FINALCUT_TEST_2' and 
    d.pfw_attempt_id=tag.pfw_attempt_id and 
    att.id=tag.pfw_attempt_id and 
    d.id=fai.desfile_id and 
    d.filetype='red_immask' and 
    concat('D00', lb.expnum)=att.unitname and 
    lb.bulb='T' and 
    fai.filename like '%_c46_%'
    order by fai.path;
