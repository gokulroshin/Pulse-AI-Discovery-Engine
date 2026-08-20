"""Initial database schema with all 5 core tables and 10 performance indexes

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-18 23:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: pipeline_runs
    op.create_table(
        'pipeline_runs',
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('stats', sa.JSON(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('run_id')
    )
    op.create_index('idx_pipeline_status', 'pipeline_runs', ['stage', 'status'], unique=False)

    # 2. Table: raw_documents
    op.create_table(
        'raw_documents',
        sa.Column('doc_id', sa.String(length=36), nullable=False),
        sa.Column('source_platform', sa.String(length=50), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('content_language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('source_url', sa.String(length=1000), nullable=True),
        sa.Column('source_subreddit', sa.String(length=100), nullable=True),
        sa.Column('author_id_hash', sa.String(length=64), nullable=True),
        sa.Column('engagement_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('inferred_category', sa.String(length=100), nullable=True),
        sa.Column('inferred_gender_context', sa.String(length=50), nullable=True),
        sa.Column('inferred_brand_tier', sa.String(length=50), nullable=True),
        sa.Column('ingestion_run_id', sa.String(length=36), nullable=True),
        sa.Column('source_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['ingestion_run_id'], ['pipeline_runs.run_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('doc_id'),
        sa.UniqueConstraint('content_hash')
    )
    op.create_index('idx_documents_platform', 'raw_documents', ['source_platform'], unique=False)
    op.create_index('idx_documents_category', 'raw_documents', ['inferred_category'], unique=False)
    op.create_index('idx_documents_hash', 'raw_documents', ['content_hash'], unique=False)

    # 3. Table: taxonomy_nodes
    op.create_table(
        'taxonomy_nodes',
        sa.Column('node_id', sa.String(length=36), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('parent_node_id', sa.String(length=36), nullable=True),
        sa.Column('extraction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('representative_quotes', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='auto_generated'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['parent_node_id'], ['taxonomy_nodes.node_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('node_id')
    )
    op.create_index('idx_taxonomy_parent', 'taxonomy_nodes', ['parent_node_id'], unique=False)

    # 4. Table: extractions
    op.create_table(
        'extractions',
        sa.Column('extraction_id', sa.String(length=36), nullable=False),
        sa.Column('doc_id', sa.String(length=36), nullable=False),
        sa.Column('reason_text', sa.Text(), nullable=False),
        sa.Column('verbatim_quote', sa.Text(), nullable=False),
        sa.Column('confidence', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('signal_type', sa.String(length=50), nullable=False),
        sa.Column('preliminary_cluster_hint', sa.String(length=100), nullable=True),
        sa.Column('taxonomy_node_id', sa.String(length=36), nullable=True),
        sa.Column('extraction_run_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['doc_id'], ['raw_documents.doc_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['taxonomy_node_id'], ['taxonomy_nodes.node_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['extraction_run_id'], ['pipeline_runs.run_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('extraction_id')
    )
    op.create_index('idx_extractions_doc', 'extractions', ['doc_id'], unique=False)
    op.create_index('idx_extractions_taxonomy', 'extractions', ['taxonomy_node_id'], unique=False)
    op.create_index('idx_extractions_signal_type', 'extractions', ['signal_type'], unique=False)

    # 5. Table: opportunity_scores
    op.create_table(
        'opportunity_scores',
        sa.Column('score_id', sa.String(length=36), nullable=False),
        sa.Column('taxonomy_node_id', sa.String(length=36), nullable=False),
        sa.Column('scoring_run_id', sa.String(length=36), nullable=True),
        sa.Column('frequency_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('triangulation_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('conversion_relevance_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('segment_breadth_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('actionability_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('composite_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('confidence_level', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('segment_breakdown', sa.JSON(), nullable=False),
        sa.Column('source_platform_breakdown', sa.JSON(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['taxonomy_node_id'], ['taxonomy_nodes.node_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scoring_run_id'], ['pipeline_runs.run_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('score_id')
    )
    op.create_index('idx_scores_rank', 'opportunity_scores', ['rank'], unique=False)
    op.create_index('idx_scores_composite', 'opportunity_scores', [sa.text('composite_score DESC')], unique=False)


def downgrade() -> None:
    op.drop_index('idx_scores_composite', table_name='opportunity_scores')
    op.drop_index('idx_scores_rank', table_name='opportunity_scores')
    op.drop_table('opportunity_scores')

    op.drop_index('idx_extractions_signal_type', table_name='extractions')
    op.drop_index('idx_extractions_taxonomy', table_name='extractions')
    op.drop_index('idx_extractions_doc', table_name='extractions')
    op.drop_table('extractions')

    op.drop_index('idx_taxonomy_parent', table_name='taxonomy_nodes')
    op.drop_table('taxonomy_nodes')

    op.drop_index('idx_documents_hash', table_name='raw_documents')
    op.drop_index('idx_documents_category', table_name='raw_documents')
    op.drop_index('idx_documents_platform', table_name='raw_documents')
    op.drop_table('raw_documents')

    op.drop_index('idx_pipeline_status', table_name='pipeline_runs')
    op.drop_table('pipeline_runs')
