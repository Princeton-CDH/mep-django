Search.setIndex({docnames:["architecture","changelog","codedocs","index"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":2,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":2,"sphinx.domains.rst":2,"sphinx.domains.std":1,"sphinx.ext.intersphinx":1,"sphinx.ext.viewcode":1,sphinx:56},filenames:["architecture.rst","changelog.rst","codedocs.rst","index.rst"],objects:{"mep.accounts":{models:[2,0,0,"-"],partial_date:[2,0,0,"-"]},"mep.accounts.management.commands":{export_events:[2,0,0,"-"],report_timegaps:[2,0,0,"-"]},"mep.accounts.models":{Account:[2,1,1,""],Address:[2,1,1,""],Borrow:[2,1,1,""],CurrencyMixin:[2,1,1,""],Event:[2,1,1,""],EventQuerySet:[2,1,1,""],Purchase:[2,1,1,""],Reimbursement:[2,1,1,""],Subscription:[2,1,1,""],SubscriptionType:[2,1,1,""]},"mep.accounts.models.Account":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],add_event:[2,3,1,""],get_events:[2,3,1,""],has_card:[2,3,1,""],list_locations:[2,3,1,""],list_persons:[2,3,1,""],member_card_images:[2,3,1,""],reimbursement_set:[2,3,1,""],subscription_set:[2,3,1,""]},"mep.accounts.models.Address":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],clean:[2,3,1,""]},"mep.accounts.models.Borrow":{DoesNotExist:[2,2,1,""],ITEM_RETURNED:[2,4,1,""],MultipleObjectsReturned:[2,2,1,""],save:[2,3,1,""]},"mep.accounts.models.CurrencyMixin":{currency_symbol:[2,3,1,""]},"mep.accounts.models.Event":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],event_label:[2,4,1,""],nonstandard_notation:[2,4,1,""]},"mep.accounts.models.EventQuerySet":{book_activities:[2,3,1,""],borrows:[2,3,1,""],generic:[2,3,1,""],known_years:[2,3,1,""],membership_activities:[2,3,1,""],purchases:[2,3,1,""],reimbursements:[2,3,1,""],subscriptions:[2,3,1,""]},"mep.accounts.models.Purchase":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],date:[2,3,1,""],save:[2,3,1,""]},"mep.accounts.models.Reimbursement":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],date:[2,3,1,""],save:[2,3,1,""],validate_unique:[2,3,1,""]},"mep.accounts.models.Subscription":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],calculate_duration:[2,3,1,""],purchase_date:[2,4,1,""],readable_duration:[2,3,1,""],save:[2,3,1,""],total_amount:[2,3,1,""],validate_unique:[2,3,1,""]},"mep.accounts.models.SubscriptionType":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.accounts.partial_date":{DatePrecision:[2,1,1,""],DatePrecisionField:[2,1,1,""],KnownYear:[2,1,1,""],PartialDate:[2,1,1,""],PartialDateFormMixin:[2,1,1,""],PartialDateMixin:[2,1,1,""]},"mep.accounts.partial_date.DatePrecisionField":{from_db_value:[2,3,1,""],to_python:[2,3,1,""],value_to_string:[2,3,1,""]},"mep.accounts.partial_date.PartialDate":{date_format:[2,3,1,""],parse_date:[2,3,1,""]},"mep.accounts.partial_date.PartialDateFormMixin":{clean:[2,3,1,""],get_initial_for_field:[2,3,1,""]},"mep.accounts.partial_date.PartialDateMixin":{calculate_date:[2,3,1,""],date_range:[2,3,1,""]},"mep.books":{models:[2,0,0,"-"],utils:[2,0,0,"-"],views:[2,0,0,"-"]},"mep.books.management.commands":{export_books:[2,0,0,"-"]},"mep.books.models":{Creator:[2,1,1,""],CreatorType:[2,1,1,""],Edition:[2,1,1,""],EditionCreator:[2,1,1,""],Format:[2,1,1,""],Genre:[2,1,1,""],PastWorkSlug:[2,1,1,""],Publisher:[2,1,1,""],PublisherPlace:[2,1,1,""],Subject:[2,1,1,""],Work:[2,1,1,""],WorkQuerySet:[2,1,1,""],WorkSignalHandlers:[2,1,1,""]},"mep.books.models.Creator":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.books.models.CreatorType":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.books.models.Edition":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],display_html:[2,3,1,""],display_text:[2,3,1,""],updated_at:[2,4,1,""]},"mep.books.models.EditionCreator":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.books.models.Format":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],uri:[2,4,1,""]},"mep.books.models.Genre":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.books.models.PastWorkSlug":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],slug:[2,4,1,""],work:[2,4,1,""]},"mep.books.models.Publisher":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.books.models.PublisherPlace":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.books.models.Subject":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],create_from_uri:[2,3,1,""],name:[2,4,1,""],rdf_type:[2,4,1,""],uri:[2,4,1,""]},"mep.books.models.Work":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],UNCERTAINTY_MESSAGE:[2,4,1,""],admin_url:[2,3,1,""],author_list:[2,3,1,""],authors:[2,3,1,""],borrow_count:[2,3,1,""],creator_by_type:[2,3,1,""],creator_names:[2,3,1,""],editors:[2,3,1,""],event_count:[2,3,1,""],first_known_interaction:[2,3,1,""],format:[2,3,1,""],generate_slug:[2,3,1,""],genre_list:[2,3,1,""],genres:[2,4,1,""],get_absolute_url:[2,3,1,""],has_uri:[2,3,1,""],index_data:[2,3,1,""],is_uncertain:[2,3,1,""],items_to_index:[2,3,1,""],mep_id:[2,4,1,""],populate_from_worldcat:[2,3,1,""],public_notes:[2,4,1,""],purchase_count:[2,3,1,""],save:[2,3,1,""],slug:[2,4,1,""],sort_author_list:[2,3,1,""],subject_list:[2,3,1,""],subjects:[2,4,1,""],translators:[2,3,1,""],updated_at:[2,4,1,""],validate_unique:[2,3,1,""]},"mep.books.models.WorkQuerySet":{count_events:[2,3,1,""]},"mep.books.models.WorkSignalHandlers":{creator_change:[2,3,1,""],creatortype_delete:[2,3,1,""],creatortype_save:[2,3,1,""],event_delete:[2,3,1,""],event_save:[2,3,1,""],format_delete:[2,3,1,""],format_save:[2,3,1,""],person_delete:[2,3,1,""],person_save:[2,3,1,""]},"mep.books.utils":{generate_sort_title:[2,5,1,""],nonstop_words:[2,5,1,""],work_slug:[2,5,1,""]},"mep.books.views":{WorkAutocomplete:[2,1,1,""],WorkCardList:[2,1,1,""],WorkCirculation:[2,1,1,""],WorkDetail:[2,1,1,""],WorkLastModifiedListMixin:[2,1,1,""],WorkList:[2,1,1,""],WorkPastSlugMixin:[2,1,1,""]},"mep.books.views.WorkAutocomplete":{get_queryset:[2,3,1,""]},"mep.books.views.WorkCardList":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_queryset:[2,3,1,""],model:[2,4,1,""]},"mep.books.views.WorkCirculation":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_queryset:[2,3,1,""],model:[2,4,1,""]},"mep.books.views.WorkDetail":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],model:[2,4,1,""]},"mep.books.views.WorkLastModifiedListMixin":{get_solr_lastmodified_filters:[2,3,1,""]},"mep.books.views.WorkList":{form_class:[2,4,1,""],get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_form:[2,3,1,""],get_form_kwargs:[2,3,1,""],get_page_labels:[2,3,1,""],get_queryset:[2,3,1,""],get_range_stats:[2,3,1,""],model:[2,4,1,""],range_field_map:[2,4,1,""],search_bib_query:[2,4,1,""],stats_fields:[2,4,1,""]},"mep.common":{models:[2,0,0,"-"],utils:[2,0,0,"-"],validators:[2,0,0,"-"],views:[2,0,0,"-"]},"mep.common.models":{AliasIntegerField:[2,1,1,""],DateRange:[2,1,1,""],Named:[2,1,1,""],Notable:[2,1,1,""],TrackChangesModel:[2,1,1,""]},"mep.common.models.AliasIntegerField":{contribute_to_class:[2,3,1,""]},"mep.common.models.DateRange":{clean:[2,3,1,""],dates:[2,3,1,""],end_year:[2,4,1,""],start_year:[2,4,1,""]},"mep.common.models.Named":{name:[2,4,1,""]},"mep.common.models.Notable":{has_notes:[2,3,1,""],note_snippet:[2,3,1,""],notes:[2,4,1,""]},"mep.common.models.TrackChangesModel":{has_changed:[2,3,1,""],initial_value:[2,3,1,""],save:[2,3,1,""]},"mep.common.utils":{abbreviate_labels:[2,5,1,""],absolutize_url:[2,5,1,""],alpha_pagelabels:[2,5,1,""],login_temporarily_required:[2,5,1,""]},"mep.common.validators":{verify_latlon:[2,5,1,""]},"mep.common.views":{AjaxTemplateMixin:[2,1,1,""],FacetJSONMixin:[2,1,1,""],LabeledPagesMixin:[2,1,1,""],LoginRequiredOr404Mixin:[2,1,1,""],RdfViewMixin:[2,1,1,""],SolrLastModifiedMixin:[2,1,1,""],VaryOnHeadersMixin:[2,1,1,""]},"mep.common.views.AjaxTemplateMixin":{ajax_template_name:[2,4,1,""],dispatch:[2,3,1,""],get_template_names:[2,3,1,""],vary_headers:[2,4,1,""]},"mep.common.views.FacetJSONMixin":{render_facets:[2,3,1,""],render_to_response:[2,3,1,""],vary_headers:[2,4,1,""]},"mep.common.views.LabeledPagesMixin":{dispatch:[2,3,1,""],get_context_data:[2,3,1,""],get_page_labels:[2,3,1,""]},"mep.common.views.LoginRequiredOr404Mixin":{handle_no_permission:[2,3,1,""]},"mep.common.views.RdfViewMixin":{add_rdf_to_context:[2,3,1,""],as_rdf:[2,3,1,""],breadcrumbs:[2,4,1,""],get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context:[2,3,1,""],get_context_data:[2,3,1,""],rdf_type:[2,4,1,""]},"mep.common.views.SolrLastModifiedMixin":{dispatch:[2,3,1,""],get_solr_lastmodified_filters:[2,3,1,""],last_modified:[2,3,1,""],solr_lastmodified_filters:[2,4,1,""]},"mep.common.views.VaryOnHeadersMixin":{dispatch:[2,3,1,""]},"mep.footnotes":{models:[2,0,0,"-"]},"mep.footnotes.models":{Bibliography:[2,1,1,""],BibliographySignalHandlers:[2,1,1,""],Footnote:[2,1,1,""],FootnoteQuerySet:[2,1,1,""],SourceType:[2,1,1,""]},"mep.footnotes.models.Bibliography":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],footnote_count:[2,3,1,""],index_data:[2,3,1,""],index_item_type:[2,3,1,""],items_to_index:[2,3,1,""],manifest:[2,4,1,""]},"mep.footnotes.models.BibliographySignalHandlers":{account_delete:[2,3,1,""],account_save:[2,3,1,""],canvas_delete:[2,3,1,""],canvas_save:[2,3,1,""],debug_log:[2,3,1,""],event_delete:[2,3,1,""],event_save:[2,3,1,""],manifest_delete:[2,3,1,""],manifest_save:[2,3,1,""],person_delete:[2,3,1,""],person_save:[2,3,1,""]},"mep.footnotes.models.Footnote":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],image_thumbnail:[2,3,1,""]},"mep.footnotes.models.FootnoteQuerySet":{event_date_range:[2,3,1,""],events:[2,3,1,""],on_events:[2,3,1,""]},"mep.footnotes.models.SourceType":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],item_count:[2,3,1,""]},"mep.people":{admin:[2,0,0,"-"],forms:[2,0,0,"-"],geonames:[2,0,0,"-"],models:[2,0,0,"-"],views:[2,0,0,"-"]},"mep.people.admin":{CountryAdmin:[2,1,1,""],CountryAdminForm:[2,1,1,""],GeoNamesLookupWidget:[2,1,1,""],InfoURLInline:[2,1,1,""],LocationAdmin:[2,1,1,""],LocationAdminForm:[2,1,1,""],MapWidget:[2,1,1,""],PersonAddressInline:[2,1,1,""],PersonAdmin:[2,1,1,""],PersonAdminForm:[2,1,1,""],PersonTypeListFilter:[2,1,1,""],RelationshipInline:[2,1,1,""],RelationshipInlineForm:[2,1,1,""]},"mep.people.admin.CountryAdmin":{form:[2,4,1,""]},"mep.people.admin.GeoNamesLookupWidget":{render:[2,3,1,""]},"mep.people.admin.InfoURLInline":{model:[2,4,1,""]},"mep.people.admin.LocationAdmin":{form:[2,4,1,""]},"mep.people.admin.LocationAdminForm":{mapbox_token:[2,4,1,""]},"mep.people.admin.MapWidget":{render:[2,3,1,""]},"mep.people.admin.PersonAdmin":{csv_filename:[2,3,1,""],export_fields:[2,4,1,""],export_to_csv:[2,3,1,""],form:[2,4,1,""],get_urls:[2,3,1,""],merge_people:[2,3,1,""],past_slugs_list:[2,3,1,""],tabulate_queryset:[2,3,1,""]},"mep.people.admin.PersonTypeListFilter":{lookups:[2,3,1,""],queryset:[2,3,1,""]},"mep.people.admin.RelationshipInline":{form:[2,4,1,""],model:[2,4,1,""]},"mep.people.forms":{MemberSearchForm:[2,1,1,""],PersonChoiceField:[2,1,1,""],PersonMergeForm:[2,1,1,""]},"mep.people.forms.PersonChoiceField":{label_from_instance:[2,3,1,""]},"mep.people.geonames":{GeoNamesAPI:[2,1,1,""],GeoNamesError:[2,2,1,""],GeoNamesUnauthorized:[2,2,1,""]},"mep.people.geonames.GeoNamesAPI":{call_api:[2,3,1,""],countries:[2,3,1,""],countries_by_code:[2,4,1,""],search:[2,3,1,""],uri_from_id:[2,3,1,""]},"mep.people.management.commands":{export_members:[2,0,0,"-"]},"mep.people.models":{Country:[2,1,1,""],InfoURL:[2,1,1,""],Location:[2,1,1,""],PastPersonSlug:[2,1,1,""],Person:[2,1,1,""],PersonQuerySet:[2,1,1,""],PersonSignalHandlers:[2,1,1,""],Profession:[2,1,1,""],Relationship:[2,1,1,""],RelationshipType:[2,1,1,""]},"mep.people.models.Country":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.people.models.InfoURL":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.people.models.Location":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],arrondissement:[2,3,1,""],arrondissement_ordinal:[2,3,1,""],city:[2,4,1,""],country:[2,4,1,""],footnotes:[2,4,1,""],latitude:[2,4,1,""],longitude:[2,4,1,""],name:[2,4,1,""],street_address:[2,4,1,""]},"mep.people.models.PastPersonSlug":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],person:[2,4,1,""],slug:[2,4,1,""]},"mep.people.models.Person":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""],account_id:[2,3,1,""],address_count:[2,3,1,""],admin_url:[2,3,1,""],birth_year:[2,4,1,""],card:[2,3,1,""],death_year:[2,4,1,""],firstname_last:[2,3,1,""],footnotes:[2,4,1,""],gender:[2,4,1,""],get_absolute_url:[2,3,1,""],has_account:[2,3,1,""],has_card:[2,3,1,""],in_logbooks:[2,3,1,""],index_data:[2,3,1,""],is_creator:[2,3,1,""],is_organization:[2,4,1,""],items_to_index:[2,3,1,""],list_nationalities:[2,3,1,""],mep_id:[2,4,1,""],name:[2,4,1,""],nationalities:[2,4,1,""],profession:[2,4,1,""],public_notes:[2,4,1,""],relations:[2,4,1,""],save:[2,3,1,""],set_birth_death_years:[2,3,1,""],short_name:[2,3,1,""],slug:[2,4,1,""],sort_name:[2,4,1,""],subscription_dates:[2,3,1,""],title:[2,4,1,""],updated_at:[2,4,1,""],validate_unique:[2,3,1,""],verified:[2,4,1,""],viaf:[2,3,1,""],viaf_id:[2,4,1,""]},"mep.people.models.PersonQuerySet":{library_members:[2,3,1,""],merge_with:[2,3,1,""]},"mep.people.models.PersonSignalHandlers":{account_delete:[2,3,1,""],account_save:[2,3,1,""],address_delete:[2,3,1,""],address_save:[2,3,1,""],country_delete:[2,3,1,""],country_save:[2,3,1,""],debug_log:[2,3,1,""],event_delete:[2,3,1,""],event_save:[2,3,1,""]},"mep.people.models.Profession":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.people.models.Relationship":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.people.models.RelationshipType":{DoesNotExist:[2,2,1,""],MultipleObjectsReturned:[2,2,1,""]},"mep.people.views":{BorrowingActivities:[2,1,1,""],CountryAutocomplete:[2,1,1,""],GeoNamesLookup:[2,1,1,""],LocationAutocomplete:[2,1,1,""],MemberCardDetail:[2,1,1,""],MemberCardList:[2,1,1,""],MemberDetail:[2,1,1,""],MemberLastModifiedListMixin:[2,1,1,""],MemberPastSlugMixin:[2,1,1,""],MembersList:[2,1,1,""],MembershipActivities:[2,1,1,""],MembershipGraphs:[2,1,1,""],PersonAutocomplete:[2,1,1,""],PersonMerge:[2,1,1,""]},"mep.people.views.BorrowingActivities":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_queryset:[2,3,1,""],model:[2,4,1,""]},"mep.people.views.CountryAutocomplete":{get_queryset:[2,3,1,""]},"mep.people.views.GeoNamesLookup":{get:[2,3,1,""],get_label:[2,3,1,""]},"mep.people.views.LocationAutocomplete":{get_queryset:[2,3,1,""]},"mep.people.views.MemberCardDetail":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_object:[2,3,1,""],model:[2,4,1,""]},"mep.people.views.MemberCardList":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_queryset:[2,3,1,""],model:[2,4,1,""]},"mep.people.views.MemberDetail":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_queryset:[2,3,1,""],model:[2,4,1,""]},"mep.people.views.MemberLastModifiedListMixin":{get_solr_lastmodified_filters:[2,3,1,""]},"mep.people.views.MembersList":{form_class:[2,4,1,""],get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_form:[2,3,1,""],get_form_kwargs:[2,3,1,""],get_page_labels:[2,3,1,""],get_queryset:[2,3,1,""],get_range_stats:[2,3,1,""],initial:[2,4,1,""],model:[2,4,1,""],range_field_map:[2,4,1,""],search_name_query:[2,4,1,""],stats_fields:[2,4,1,""]},"mep.people.views.MembershipActivities":{get_absolute_url:[2,3,1,""],get_breadcrumbs:[2,3,1,""],get_context_data:[2,3,1,""],get_queryset:[2,3,1,""],model:[2,4,1,""]},"mep.people.views.MembershipGraphs":{model:[2,4,1,""]},"mep.people.views.PersonAutocomplete":{get_queryset:[2,3,1,""],get_result_label:[2,3,1,""]},"mep.people.views.PersonMerge":{form_class:[2,4,1,""],form_valid:[2,3,1,""],get_form_kwargs:[2,3,1,""],get_initial:[2,3,1,""],get_success_url:[2,3,1,""]},mep:{accounts:[2,0,0,"-"],books:[2,0,0,"-"],common:[2,0,0,"-"],footnotes:[2,0,0,"-"],people:[2,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","exception","Python exception"],"3":["py","method","Python method"],"4":["py","attribute","Python attribute"],"5":["py","function","Python function"]},objtypes:{"0":"py:module","1":"py:class","2":"py:exception","3":"py:method","4":"py:attribute","5":"py:function"},terms:{"100yearsagotodai":1,"12month":2,"2px":1,"4th":1,"6month":2,"abstract":2,"boolean":[0,2],"break":[1,2],"case":[1,2],"class":2,"default":[1,2,3],"export":1,"final":3,"function":[0,2],"import":[0,2],"long":1,"new":[0,1,2],"null":2,"public":[1,2,3],"return":[0,1,2],"short":2,"static":[2,3],"switch":3,"true":2,Added:1,CMS:[0,3],For:[],One:[1,2],The:[0,2,3],Then:3,There:0,These:0,Use:2,Used:2,Uses:2,With:2,_kwarg:2,_or_:2,_other_:2,_set:2,_to_:2,a11i:3,abbrevi:2,abbreviate_label:2,abl:1,about:[1,2],abov:1,absolut:2,absolutize_url:2,accent:1,accept:[1,2],access:[1,2],accessibi:1,accident:1,accommod:0,account:1,account_delet:2,account_id:2,account_sav:2,account_year:2,accuont:1,accur:1,across:2,action:2,activ:[1,2,3],actual:[0,1],adapt:2,add:[0,2,3],add_ev:2,add_rdf_to_context:2,added:[1,2],addit:0,address:[0,1,2],address_count:2,address_delet:2,address_sav:2,adjust:1,admin:3,admin_sit:2,admin_url:2,administr:1,affect:1,after:[1,2,3],against:[1,2],ajax:2,ajax_template_nam:2,ajaxtemplatemixin:2,alia:2,alias:2,aliasintegerfield:2,all:[0,1,2,3],allow:[0,1,2],alpha_pagelabel:2,alphabet:[1,2],alreadi:2,also:[1,3],altern:3,alwai:2,ambigu:1,amount:[1,2],analyt:1,analyz:1,anchor:1,ani:[0,1,2],annot:2,anoth:2,ansibl:1,anywher:2,apach:3,api:2,apostroph:2,app:2,appear:1,applic:[2,3],appropri:[2,3],architectur:3,archiv:[1,3],ard:2,aren:2,arg:2,argument:2,aria:1,around:2,arrondiss:[1,2],arrondissement_ordin:2,art:2,as_rdf:2,ask:2,assert:[1,2],asset:3,assist:2,associ:[0,1,2],attach:1,attr:2,attr_meth:2,attribut:2,atyp:1,author:[0,1,2],author_list:2,auto_cr:2,auto_id:2,autocomplet:[1,2],autodetect:1,autom:3,automat:[1,3],autopopul:1,avail:[1,2,3],avoid:[1,2],back:1,backend:2,backup:1,base:[1,2,3],basic:2,bce:1,beach:[1,2,3],becaus:[1,2],been:[0,1,2],befor:[1,2],behavior:2,being:2,belong:[0,1,2],best:1,better:1,between:[0,1,2,3],beyond:1,bib:2,bib_pf:2,bib_qf:2,bib_queri:2,bibliograph:[1,2],bibliographi:[0,1,2],bibliographic_not:2,bibliographysignalhandl:2,bin:3,biograph:1,biographi:1,birth:[1,2],birth_year:2,blank:[1,2],block:1,blockquot:1,book:1,book_act:2,bookstor:3,borrow:[0,1,2],borrow_count:2,borrowingact:2,both:[0,1,2],bought:[0,1,2],boughtfor:2,branch:3,breadcrumb:[1,2],brief:2,bring:1,broken:[0,1],brows:[1,2],browser:2,bugfix:1,build:3,bulk:[1,2],cach:2,calcul:[1,2],calculate_d:2,calculate_dur:2,call:[2,3],call_api:2,callabl:2,can:[0,1,2,3],candid:2,canva:[0,2],canvas:[0,1],canvas_delet:2,canvas_sav:2,card:[0,2],care:2,categor:1,categori:1,caus:1,center:1,central:2,chang:[1,2,3],change_list:2,check:[1,2],choic:[0,2],choos:1,chore:1,chown:3,chronolog:1,circul:[1,2],circulation_d:2,citat:[1,2],citi:2,classmethod:2,clean:2,cleanup:1,clerk:1,click:1,client:2,cls:2,code:[1,3],collaps:1,collect:3,colon:2,combin:1,comma:2,command:[1,3],commit:3,commmon:3,common:0,compani:3,compar:1,comparison:1,compil:3,complet:[1,2,3],complex:0,composit:1,condit:[1,2],config:2,configset:[1,3],configur:[1,2,3],connect:2,consist:1,consolid:2,constraint:2,construct:2,consult:3,contain:0,content:[1,2,3],context:[1,2],continu:1,contribute_to_class:2,control:[1,2,3],conveni:[2,3],convent:2,convert:[0,1,2],coordin:[1,2],copi:[2,3],core:[2,3],correct:[1,2],correctli:[1,3],correspond:2,count:[1,2],count_ev:2,counter:1,countri:[1,2],countries_by_cod:2,country_delet:2,country_sav:2,countryadmin:2,countryadminform:2,countryautocomplet:2,countryinfojson:2,craw:3,creat:[1,2,3],create_from_uri:2,creator:[0,1,2],creator_by_typ:2,creator_chang:2,creator_nam:2,creator_typ:2,creatortyp:[0,2],creatortype_delet:2,creatortype_sav:2,criteria:1,cross:2,css:3,csv:[0,1,2],csv_filenam:2,currenc:[1,2],currency_symbol:2,currencymixin:2,current:[0,1,2,3],custom:[0,1,2,3],dai:[0,1,2],dashboard:[1,3],data:[0,2,3],databas:[1,2,3],dataset:2,date:[0,1],date_field:2,date_format:2,date_precision_field:2,date_rang:2,dateprecis:2,dateprecisionfield:2,daterang:[1,2],datetim:2,datev:2,davila:0,db_column:2,db_index:2,db_tablespac:2,death:[1,2],death_year:2,debug:[2,3],debug_log:2,deciaml:2,deciph:1,decis:1,decor:2,deep:1,defer:1,defin:2,definit:3,degre:2,delet:[1,2],demerg:[1,2],demograph:1,deni:2,depend:[0,3],deploi:1,deploynot:3,deposit:[1,2],describ:[1,2],descript:1,descriptor:2,design:1,detail:[1,2],detect:2,determin:1,dev:3,dict:2,dictionari:2,differ:[1,2],differenti:1,difficult:1,digit:[0,1,2,3],directori:[0,3],disabl:1,disambigu:2,discov:1,dispatch:2,displai:[1,2,3],display_html:2,display_text:2,distinct:2,distinguish:[1,2],div:2,django:[0,1,2],djangosnippet:2,djiffi:[0,2],doc:[0,3],document:[0,1],doe:[0,1,2,3],doesn:[1,2],doesnotexist:2,doing:1,don:1,down:1,download:[1,2],dropdown:1,dump:0,duplic:[1,2],durat:[0,1,2],each:2,earlier:[],earliest:2,earliest_d:1,easi:1,easier:[1,3],easili:1,edismax:2,edit:[0,1,2,3],editioncr:2,editor:[0,1,2],editori:1,effect:3,effici:1,els:1,elsewher:1,embed:[1,2],emphas:1,emphasi:1,empti:[1,2],empty_label:2,empty_permit:2,enabl:[1,2,3],end:[0,1,2],end_year:2,enough:[1,2],ensur:[2,3],entail:2,enter:1,entiti:0,environ:3,equal:2,equival:2,error:[1,2],error_class:2,error_messag:2,errorlist:2,especi:1,essai:1,etc:[1,2],etyp:2,euripid:1,evalu:2,even:[1,2],event_count:2,event_date_rang:[1,2],event_delet:2,event_label:2,event_sav:2,event_year:2,eventqueryset:2,eventu:1,everi:[1,2],evid:1,exact:1,examin:1,exampl:[2,3],except:2,exclud:[1,2],exist:[1,2,3],expand:1,expatri:3,expect:2,explic:2,explicit:2,explor:1,export_field:2,export_to_csv:2,expos:1,express:2,extend:2,facet:[1,2],facetjsonmixin:2,fail:2,fall:2,fals:2,faster:1,featur:1,feature_class:2,feature_cod:2,fetch:2,few:2,field:[0,1,2],figgi:1,file:[1,2,3],filenam:2,filter:[1,2],find:[1,2],first:[1,2,3],first_known_interact:2,firstnam:2,firstname_last:2,fixtur:3,flag:[0,1,2],flash:1,flavor:3,focu:1,folder:3,follow:[2,3],foo:2,footer:1,footnot:1,footnote_count:2,footnotequeryset:2,force_insert:2,force_upd:2,foreign:0,form:1,form_class:2,form_valid:2,format:[1,2],format_delet:2,format_sav:2,former:2,forward:2,found:[1,2,3],fourth:1,fraction:0,franc:1,frech:2,from:[0,1,2,3],from_db_valu:2,front:1,frontend:3,full:[1,2],func:2,galleri:1,gap:[1,2],gender:[1,2],gener:[0,1,2,3],generate_slug:2,generate_sort_titl:2,genr:[1,2],genre_list:2,geonames_id:2,geonames_usernam:2,geonamesapi:2,geonameserror:2,geonameslookup:2,geonameslookupwidget:2,geonamesunauthor:2,get:[1,2],get_absolute_url:2,get_breadcrumb:2,get_context:2,get_context_data:2,get_ev:2,get_form:2,get_form_kwarg:2,get_initi:2,get_initial_for_field:2,get_label:2,get_object:2,get_page_label:2,get_queryset:2,get_rang:2,get_range_stat:2,get_result_label:2,get_solr_lastmodified_filt:2,get_success_url:2,get_template_nam:2,get_url:2,gift:2,git:3,github:3,give:1,given:2,glanc:1,global:1,goe:1,googl:1,graph:[1,2],greater:2,group:1,habit:1,haeder:2,handl:[1,2],handle_no_permiss:2,handler:[1,2],handwrit:1,happen:1,has:[0,1,2,3],has_account:2,has_card:2,has_chang:2,has_not:2,has_uri:2,have:[0,1,2,3],head:1,header:[1,2],hear:1,height:1,help:[1,2],help_text:2,helper:2,her:1,here:2,hidden:2,hierarchi:1,hint:2,histor:1,histori:1,holder:1,home:1,homepag:1,horizont:1,hot:3,hotel:2,hover:1,how:1,html:[2,3],http404:2,http:[2,3],human:[2,3],icon:[1,2],id_:2,idea:1,identifi:[1,2],idiosyncrasi:1,ids:2,ignor:1,iiif:[0,2],imag:[1,2],image_thumbnail:2,implement:[0,2],import_logbook:1,in_logbook:2,inaccess:3,includ:[0,1,2,3],inclus:2,incomplet:[1,2],incorrect:1,incorrectli:1,index:[2,3],index_data:2,index_item_typ:2,indic:[0,1,2],individu:[1,2],info:3,inform:[0,1,2,3],infourl:[0,2],infourlinlin:2,inherit:[0,2],initi:[2,3],initial_valu:2,inlin:2,input:[1,2],insecur:3,insensit:2,insert:2,insight:1,insist:2,instal:[1,3],instanc:[2,3],instanti:2,instead:[1,2],instruct:1,integ:2,intend:2,interact:[1,2],interest:1,interfac:1,interpret:1,invalid:1,investig:1,irregular:1,is_creat:2,is_organ:2,is_uncertain:2,isn:[1,2],issu:[2,3],item:[0,2,3],item_count:2,item_return:2,items_to_index:2,iter:[2,3],its:1,javascript:[1,3],jest:3,joint:1,json:2,jsonld:2,jsonrespons:2,june:0,just:[1,2],keep:[1,2],kei:[0,2],keyword:[1,2],kind:[1,2],know:[1,2],known:[0,2],known_year:2,knownyear:2,kwarg:2,label:[1,2],label_from_inst:2,label_suffix:2,labeledpagesmixin:2,lambda:2,land:1,larg:[1,2],larger:1,last:[1,2],last_dat:1,last_modifi:2,lastnam:2,latest:2,latitud:[1,2],lead:[1,2],leaflet:[1,2],learn:1,left:1,lend:[0,1,2,3],less:0,letter:2,level:1,lhs:2,librari:[0,1,2,3],library_memb:2,lifetim:1,light:2,like:[1,2],limit:0,limit_choices_to:2,line:[1,3],link:[0,1,2],linkabl:1,linux:3,list:2,list_loc:2,list_nation:2,list_person:2,list_view:2,live:1,load:[1,2,3],loan:2,local:[2,3],local_set:3,local_url:2,localhost:3,locat:[0,1,2,3],locationadmin:2,locationadminform:2,locationautocomplet:2,log:[2,3],logbook:[0,2],logic:[1,2],login:[1,2],login_temporarily_requir:2,loginrequiredmixin:2,loginrequiredor404:2,loginrequiredor404mixin:2,longer:1,longitud:[1,2],look:[1,2],lookup:2,lose:1,lost:1,m2m:2,maco:3,made:[0,1,3],mai:[1,2,3],main:[1,2,3],maintain:1,make:[1,2,3],malfunct:1,manag:[1,3],mani:[1,2],manifest:[0,1,2],manifest_delet:2,manifest_sav:2,manual:[1,3],map:[1,2,3],mapbox:2,mapbox_token:2,mapwidget:2,mariadb:3,mark:1,markup:1,match:[1,2],materi:1,max:2,max_char:2,max_length:2,max_row:2,max_word:2,media:1,meet:0,member_card_imag:2,membercarddetail:2,membercardlist:2,memberdetail:2,memberlastmodifiedlistmixin:2,memberpastslugmixin:2,membersearchform:2,membership:[1,2],membership_act:2,membership_d:2,membershipact:2,membershipgraph:2,membershiplist:2,memberslist:2,menu:1,mep:2,mep_id:2,mepid:2,merg:2,merge_peopl:2,merge_with:2,messag:2,metadata:1,method:[1,2,3],mezzanin:0,middl:2,migrat:[1,2],min:2,minifi:3,minim:[1,2],minimum:2,minor:1,misconfigur:1,misl:1,miss:[0,1],mixin:2,mobil:1,mode:2,model:0,model_admin:2,modeladmin:2,modif:0,modifi:[1,2],modul:[0,3],month:[0,1,2],more:[0,1,2,3],most:[1,3],much:1,multi:2,multipl:[1,2],multipleobjectsreturn:2,multit:0,multivolum:1,must:[2,3],mysql:[0,3],mysql_tzinfo_to_sql:3,name:[0,1,2],name_pf:2,name_qf:2,name_queri:2,name_start:2,nation:[1,2],navig:[1,2,3],necessari:1,necessarili:2,need:[1,3],neg:1,never:1,nice:2,node:3,non:[0,1,2],none:2,nonstandard:2,nonstandard_not:2,nonstop_word:2,normal:2,not_provid:2,notabl:2,notat:2,note:[1,2,3],note_snippet:2,notic:1,now:[0,1,2],npm:3,number:[1,2],numer:[1,2],obj:2,object:2,obsolet:1,occur:[1,2],oclc:[1,2],off:[1,3],omit:0,on_ev:2,onc:1,one:[0,1,2],ones:1,onli:[1,2],open:1,openrefin:1,oper:2,option:[0,1,2,3],order:[0,1,2,3],ordereddict:2,ordin:2,org:[1,2],organ:[0,2],origin:3,other:2,otherwis:[1,2],our:2,out:[0,1,2],output:2,over:[1,2],overal:0,overdu:1,overrid:2,overridden:2,overview:1,pa11i:3,pace:1,page:[0,1,2,3],pagin:[1,2],paid:[1,2],paragraph:1,param:2,paramet:2,parent_model:2,pari:[1,2,3],pars:2,parse_d:2,part:[1,2],partial:[0,1],partial_d:2,partiald:2,partialdateformmixin:2,partialdatemixin:[0,2],particular:[1,2],pass:2,password:3,past:[1,2],past_slugs_list:2,pastpersonslug:2,pastworkslug:2,patch:2,path:[1,2,3],patron:1,pattern:1,peopl:1,people_merge_filt:2,per:0,period:[1,2],periodicalsubscript:2,permiss:[2,3],person:2,person_delet:2,person_sav:2,personaddressinlin:2,personadmin:2,personadminform:2,personautocomplet:2,personchoicefield:2,personmerg:2,personmergeform:2,personqueryset:2,personsignalhandl:2,persontypelistfilt:2,pick:3,pip:3,pipelin:1,place:[1,2],placement:1,polici:1,popul:[1,2,3],popular:1,populate_from_worldcat:2,portion:1,possibl:[1,2],post:[1,2],postal:[1,2],preced:2,precis:[0,2],prefer:2,prefetch:2,prefix:2,prepar:1,present:[0,1,2],preserv:2,prevent:[1,2],preview:1,previou:[1,2],previous:[2,3],price:[0,1,2],primari:[1,2],primary_kei:2,prior:0,privat:2,private_onli:2,privileg:3,probabl:3,problem:1,process:[1,2],prod:3,product:3,profess:[1,2],project:[0,1,2,3],promin:1,promot:1,prompt:3,properli:1,properti:2,proven:1,provid:[0,1,2],public_not:2,publicli:2,publish:[1,2,3],publisherplac:2,pull:2,punctuat:2,purchas:[0,2],purchase_count:2,purchase_d:2,push:3,put:2,python3:3,python:[2,3],queri:[1,2],queryset:2,querystr:2,quickli:1,rais:2,rang:[1,2],range_field_map:2,rather:[0,1,2],raw:2,rdf:2,rdf_type:2,rdflib:2,rdfviewmixin:2,reactiv:1,read:[1,2],readabl:2,readable_dur:2,reassoci:2,rebuild:3,receiv:1,recent:1,recogn:1,recommend:3,reconcili:1,record:[0,1,2],redirect:[1,2],refactor:0,refer:1,referenc:[1,2],refin:1,reflect:[1,3],refund:1,regardless:1,regist:2,regular:1,reimbersu:2,reimburs:[0,1,2],reimbursement_set:2,reindex:2,rel:2,relabel:1,relat:[0,1,2],relationship:[0,1,2],relationshipinlin:2,relationshipinlineform:2,relationshiptyp:2,releas:[1,3],relev:[1,2],reload:3,remain:0,rememb:3,remov:[0,1,2],renam:[0,1],render:2,render_facet:2,render_forward_conf:2,render_to_respons:2,renew:2,replac:1,report_timegap:2,repositori:[],repres:[1,2],represent:2,request:2,requir:[0,1,2,3],research:1,reset:[1,2],resolv:[1,2],respect:2,respond:2,respons:2,restart:3,restor:1,restrict:[0,1,2],result:[1,2],retrict:2,retriev:2,retyp:1,revers:2,review:1,revis:1,rhs:2,right:1,role:[1,2],root:3,run:[2,3],runserv:3,same:[0,1,2],sampl:3,sandco:3,sandcodev:3,save:2,sbgift:2,scalabl:1,scan:1,schema:[1,2,3],scheme:2,scholarli:1,script:1,scroll:1,scss:3,search:[1,2,3],search_bib_queri:2,search_name_queri:2,secret_kei:3,section:1,secur:1,see:[1,3],select:[1,2],self:2,semant:1,semi:2,semicolon:2,sender:2,separ:[2,3],serial:2,serv:3,server:[1,2,3],session:2,set:[1,2,3],set_birth_death_year:2,setup:3,setup_site_pag:3,sever:0,sex:1,shakespear:[1,2,3],share:[2,3],shift:0,short_nam:2,shorten:2,should:[1,2],show:[1,2],shown:1,sight:1,signal:[1,2],simpl:2,simplic:0,simplifi:[1,2],sinc:2,singl:[1,2],site:[1,2],sitemap:[1,3],size:1,skip:2,slug:[1,2],smart:2,snippet:2,social:1,soldfor:2,solr:[2,3],solr_conf:3,solr_connect:3,solr_lastmodified_filt:2,solr_schema:3,solrlastmodifiedmixin:2,solrqueryset:2,some:[2,3],someth:[1,2],soon:1,sort:[1,2],sort_author_list:2,sort_nam:2,sourc:[1,2,3],source_typ:2,sourcemap:3,sourcetyp:2,space:[1,2],specif:[0,1,2],specifi:2,sphinx:[0,3],split:[0,2],sql:2,stai:1,standard:[0,1,2],start:[0,1,2,3],start_dat:2,start_year:2,stat:2,statement:1,stats_field:2,statu:[0,1],still:[0,1],stop:2,stopword:[1,2],store:1,str:2,stream:2,streamlin:1,street:2,street_address:2,strftime:2,strikethru:2,string:2,structur:2,stub:[1,2,3],style:1,sub_typ:0,subcategori:1,subclass:2,subject:[1,2],subject_list:2,submiss:2,subscrib:0,subscript:[0,1,2],subscription_d:2,subscription_set:2,subscriptiontyp:[0,2],subset:1,subtyp:2,success:2,suitabl:2,summari:2,superscript:[1,2],suppli:2,support:[0,1,2],sure:3,svg:1,sylvia:[1,2,3],symbol:2,sync:1,syntax:[1,2],system:[1,2],tab:1,tabl:[0,1,2],tabular:2,tabulate_queryset:2,tag:[1,2],taglin:1,take:[1,3],task:1,team:1,technolog:2,tell:1,templat:[1,2],temporarili:1,term:[1,2],test:2,testcas:2,text:[1,2],than:[0,1,2],thei:[1,2],them:[1,2,3],thi:[0,1,2,3],thing:3,third:1,those:[1,2],through:[1,2],thumbnail:[1,2],tied:2,tight:2,tile:1,time:[1,2,3],timelin:1,timeout:1,timestamp:[1,2],timezon:3,titl:[1,2],to_field_nam:2,to_python:2,todo:2,togeth:2,toggl:1,token:2,tool:3,toolbar:3,tooltip:1,top:1,total:[1,2],total_amount:2,town:2,track:[0,1],trackchangesmodel:2,transcript:1,translat:[0,1,2],trap:1,travi:3,trigger:1,tupl:2,turn:3,tweet:1,twice:1,two:[1,2],txt:3,type:[0,1,2],typescript:1,unauthor:2,unavail:1,unborrow:1,uncategor:1,uncertain:2,uncertainti:2,uncertainty_messag:2,uncertaintyicon:2,unclear:[1,2],under:3,underscor:1,understand:1,unidentifi:1,union:2,uniqu:[1,2],unique_for_d:2,unique_for_month:2,unique_for_year:2,unique_togeth:2,unknown:2,unknown_year:2,unless:1,unneed:1,unset:2,unstabl:1,unstyl:1,until:1,unus:1,unusu:1,updat:[1,2,3],updated_at:2,uri:[1,2],uri_from_id:2,uriref:2,url:[0,1,2,3],urlconf:2,usag:2,use:[0,1,2,3],use_required_attribut:2,used:[0,1,2],user:[1,2,3],usernam:2,using:[1,2,3],usr:3,util:3,valid:0,validate_uniqu:2,validationerror:2,valu:2,value_to_str:2,vari:[2,3],variant:1,variat:[0,1],vary_head:2,vary_on_head:2,varyonheadersmixin:2,verbos:2,verbose_nam:2,verifi:[1,2],verify_latlon:2,version:[1,2],via:[1,2],viaf:[1,2],viaf_id:2,viafent:2,viapi:2,view:1,viewer:[1,2],virtualenv:3,visibl:1,visual:1,volum:[1,2],wagtail:[2,3],wai:1,want:[1,2,3],web:3,webpack:[1,3],webpag:2,websit:[1,2],week:2,well:[0,1,2],were:[0,1,2],what:1,whatev:1,when:[1,2,3],where:[1,2],whether:2,which:[0,1,2,3],who:[1,2],wide:1,widget:2,wikipedia:[1,2],window:3,winthrop:2,within:2,without:[1,3],word:2,work:[0,1,2,3],work_slug:2,workautocomplet:2,workcardlist:2,workcircul:2,workdetail:2,worklastmodifiedlistmixin:2,worklist:2,workpastslugmixin:2,workqueryset:2,worksearchform:2,worksignalhandl:2,worktre:3,worldcat:2,worldcat_ent:2,would:1,wrap:2,wrapper:2,written:3,wrong:1,xml:[1,2],year:[1,2],you:[2,3],your:3,zone:3,zoneinfo:3},titles:["Architecture","CHANGELOG","Code Documentation","mep-django documentation"],titleterms:{"export":2,"function":1,"import":1,CMS:1,access:3,account:[0,2],add:1,admin:[1,2],architectur:0,basic:1,book:[0,2],card:1,chang:0,changelog:1,code:2,command:2,common:2,data:1,databas:0,date:2,design:0,detail:0,develop:3,diagram:0,django:3,document:[2,3],enhanc:1,entri:1,event:[0,1,2],fix:1,footnot:[0,2],form:2,geonam:2,improv:1,indic:3,initi:[0,1],instruct:3,issu:1,item:1,known:1,licens:3,list:1,logbook:1,manag:2,member:[1,2],mep:3,merg:1,model:2,other:1,overview:0,partial:2,peopl:[0,2],person:[0,1],personographi:1,previou:0,purchas:1,report:[1,2],schema:0,solr:1,tabl:3,test:3,timegap:2,unit:3,updat:0,util:2,valid:2,variou:1,version:0,view:2,wagtail:[0,1]}})