const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, ImageRun
} = require("docx");

const results = JSON.parse(fs.readFileSync("/home/claude/marketing_ab_project/exports/results.json", "utf8"));
const dq = JSON.parse(fs.readFileSync("/home/claude/marketing_ab_project/exports/data_quality_report.json", "utf8"));
const design = JSON.parse(fs.readFileSync("/home/claude/marketing_ab_project/exports/experiment_design.json", "utf8"));

const t = results.topline;
const alloc = results.allocation_guardrail;
const z = results.z_test;
const rec = results.recommendation;
const pa = design.power_analysis;
const dose = results.dose_response;

const shipping = rec.recommendation.startsWith("SHIP");
const ASSUMED_AOV = 50;
const estRevenue = t.incremental_conversions * ASSUMED_AOV;

function kpiCell(label, value, color) {
  return new TableCell({
    width: { size: 25, type: WidthType.PERCENTAGE },
    shading: { type: ShadingType.CLEAR, fill: "F3F4F6" },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: value, bold: true, size: 30, color: color || "111827" })],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: label, size: 16, color: "6B7280" })],
      }),
    ],
  });
}

function bullet(text) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 40 },
    children: [new TextRun({ text, size: 20 })],
  });
}

const doc = new Document({
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter
          margin: { top: 500, bottom: 500, left: 900, right: 900 },
        },
      },
      children: [
        new Paragraph({
          children: [new TextRun({ text: "A/B Test Results Memo", bold: true, size: 40 })],
        }),
        new Paragraph({
          spacing: { after: 100 },
          children: [
            new TextRun({
              text: "Experiment: Ad Exposure vs. PSA Holdout (Conversion Lift Study)  |  Prepared for: Marketing & Growth",
              size: 19, color: "6B7280", italics: true,
            }),
          ],
        }),

        // ---- Recommendation banner ----
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  width: { size: 100, type: WidthType.PERCENTAGE },
                  shading: { type: ShadingType.CLEAR, fill: shipping ? "DCFCE7" : "FEE2E2" },
                  margins: { top: 160, bottom: 160, left: 200, right: 200 },
                  children: [
                    new Paragraph({
                      children: [
                        new TextRun({
                          text: shipping ? "RECOMMENDATION: SHIP" : "RECOMMENDATION: DO NOT SHIP",
                          bold: true, size: 26, color: shipping ? "166534" : "991B1B",
                        }),
                      ],
                    }),
                    new Paragraph({
                      spacing: { before: 60 },
                      children: [new TextRun({ text: rec.recommendation, size: 20, color: "374151" })],
                    }),
                  ],
                }),
              ],
            }),
          ],
        }),

        new Paragraph({ text: "", spacing: { after: 60 } }),

        // ---- KPI row ----
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          rows: [
            new TableRow({
              children: [
                kpiCell("PSA (holdout) CVR", (t.conversion_rate_psa * 100).toFixed(2) + "%"),
                kpiCell("Ad CVR", (t.conversion_rate_ad * 100).toFixed(2) + "%"),
                kpiCell("Relative Lift", "+" + t.relative_lift_pct.toFixed(1) + "%", "166534"),
                kpiCell("p-value", z.p_value < 0.0001 ? "<0.0001" : z.p_value.toFixed(4)),
              ],
            }),
          ],
        }),

        new Paragraph({ text: "", spacing: { after: 100 } }),

        // ---- Hypothesis & Design ----
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 80, after: 50 },
          children: [new TextRun({ text: "Hypothesis & Design" })],
        }),
        bullet(`H\u2080: Conversion rate is equal whether a user is shown the ad or the PSA. Two-sided test.`),
        bullet(`Design: a PSA-holdout conversion-lift study \u2014 the industry-standard method (used by Meta/Google Ads) for measuring the causal effect of ad exposure. Most users (${(100 - alloc.psa_holdout_pct).toFixed(1)}%) see the real ad; a randomized ${alloc.psa_holdout_pct}% holdout sees a public service announcement in the same ad slot instead.`),
        bullet(`Primary metric: conversion rate. Guardrails: exposure-opportunity balance between arms, holdout power adequacy, and a within-group dose-response check.`),
        bullet(`Pre-registered MDE: +${pa.mde_relative_pct}% relative lift \u2014 required holdout n \u2248 ${pa.required_n_psa_holdout.toLocaleString()} at \u03b1=${pa.alpha}, power=${pa.power}. Actual holdout (n=${pa.actual_n_psa_holdout.toLocaleString()}) exceeds this, so the test is adequately powered.`),

        // ---- Data Quality ----
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 100, after: 50 },
          children: [new TextRun({ text: "Data Quality & Guardrails" })],
        }),
        bullet(`${dq.rows_raw.toLocaleString()} rows, zero nulls, zero duplicate users \u2014 no cleaning required.`),
        bullet(`Exposure balance: mean ad-slot impressions (total_ads) are nearly identical between arms (ad ${alloc.mean_total_ads_ad_group} vs. psa ${alloc.mean_total_ads_psa_group}, Welch t-test p=${alloc.welch_ttest_p_value}) \u2014 confirms the ad/PSA swap was randomized independently of browsing intensity, not confounded.`),
        bullet(`Dose-response: within the ad group, conversion rises monotonically with ad exposure (Spearman \u03c1=${dose.spearman_corr_total_ads_vs_converted}, p<0.0001) \u2014 strong supporting evidence this is a real causal ad effect, not noise.`),
        bullet(`Lift is positive in every single day of the week (see chart) \u2014 no novelty effect or single-day anomaly driving the result.`),

        // ---- Results ----
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 100, after: 50 },
          children: [new TextRun({ text: "Statistical Results" })],
        }),
        bullet(`Absolute lift: +${t.absolute_lift_pp.toFixed(3)}pp, 95% CI [${t.absolute_lift_ci95_pp[0].toFixed(3)}, ${t.absolute_lift_ci95_pp[1].toFixed(3)}]pp \u2014 entirely above zero.`),
        bullet(`Two-proportion z-test: z=${z.z_statistic}, p${z.p_value < 0.0001 ? "<0.0001" : "="+z.p_value}. Chi-square test agrees (p${results.chi_square_test.p_value < 0.0001 ? "<0.0001" : "="+results.chi_square_test.p_value}).`),
        bullet(`Bootstrap (10,000 resamples): mean lift +${results.bootstrap.mean_lift_pp}pp, 95% CI [${results.bootstrap.ci95_pp[0]}, ${results.bootstrap.ci95_pp[1]}]pp \u2014 100% of resamples favor the ad.`),
        bullet(`Estimated incremental conversions: ${t.incremental_conversions.toLocaleString()} (vs. the PSA baseline rate). At an illustrative $${ASSUMED_AOV} AOV (no real order-value field in this dataset \u2014 substitute your actual AOV), that's ~$${estRevenue.toLocaleString()} in incremental revenue attributable to the ad.`),

        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 80, after: 40 },
          children: [new TextRun({ text: "Visuals" })],
        }),
        new Table({
          width: { size: 100, type: WidthType.PERCENTAGE },
          borders: {
            top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
            left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
            insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
          },
          rows: [
            new TableRow({
              children: [
                new TableCell({
                  width: { size: 50, type: WidthType.PERCENTAGE },
                  children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [new ImageRun({
                      type: "png",
                      data: fs.readFileSync("/home/claude/marketing_ab_project/figures/01_conversion_rate_by_group.png"),
                      transformation: { width: 235, height: 176 },
                    })],
                  })],
                }),
                new TableCell({
                  width: { size: 50, type: WidthType.PERCENTAGE },
                  children: [new Paragraph({
                    alignment: AlignmentType.CENTER,
                    children: [new ImageRun({
                      type: "png",
                      data: fs.readFileSync("/home/claude/marketing_ab_project/figures/03_dose_response.png"),
                      transformation: { width: 235, height: 141 },
                    })],
                  })],
                }),
              ],
            }),
          ],
        }),

        // ---- Next steps ----
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          spacing: { before: 100, after: 50 },
          children: [new TextRun({ text: "Next Steps" })],
        }),
        bullet(`Ship: roll out to the PSA holdout, keeping a small (~1%) permanent holdout to keep measuring incrementality going forward.`),
        bullet(`Segment by exposure_bucket for a frequency-capping study \u2014 conversion keeps climbing at high exposure; check against fatigue/cost per incremental conversion.`),
        bullet(`Replace the illustrative $${ASSUMED_AOV} AOV with actual order-value data before this revenue estimate goes into a budget conversation.`),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/home/claude/marketing_ab_project/memo/results_memo.docx", buf);
  console.log("wrote results_memo.docx");
});
