-- simple summary of interventions table, where any instance of multiple types is classified as Multiple
create table interventions_simple_mod as
select nct_id, 
  case when count(distinct intervention_type) = 1 then min(intervention_type) else 'Multiple' end intervention_type
from interventions
group by nct_id;

create index interventions_simple_mod_nct_id_idx on interventions_simple_mod(nct_id);

-- more complex summary of interventions table, where we also remove control and placebo categories to see if the treatment(s) are the same type
create table interventions_complex_mod as
select i.nct_id,
  case when count(distinct intervention_type) = 1 then min(intervention_type)
       when count(distinct case when arm_group_type not in ('Control','No Intervention','Placebo Comparator','Sham Comparator') then intervention_type end) = 1
         then min(case when arm_group_type not in ('Control','No Intervention','Placebo Comparator','Sham Comparator') then intervention_type end)
       else 'Multiple' end intervention_type
from interventions i 
  left join intervention_arm_groups ia on i.intervention_id=ia.intervention_id
  left join arm_groups ag on i.nct_id=ag.nct_id and ia.arm_group_label=ag.arm_group_label
group by i.nct_id;

create index interventions_complex_mod_nct_id_idx on interventions_complex_mod(nct_id);

-- summary of sponsors 
create table sponsors_mod as
select nct_id, 
  max(case when sponsor_type = 'Lead Sponsor' then agency end) agency,
  max(case when sponsor_type = 'Lead Sponsor' then agency_class end) agency_class,
  max(case when agency_class = 'Industry' then 'Y' else 'N' end) any_industry,
  count(*) num_sponsors
from sponsors
group by nct_id;

create index sponsors_mod_nct_id_idx on sponsors_mod(nct_id);

