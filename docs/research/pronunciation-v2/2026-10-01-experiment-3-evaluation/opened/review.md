# Experiment 3 evaluation

Primary evidence: ALL 18 source-declared speakers / ALL 720 sealed clips. No exclusions.
Raw probabilities are uncalibrated; no abstention or confidence threshold.

Preregistered promising rule: False.
Failed conditions: pooled_accuracy_non_regression, pooled_balanced_accuracy_non_regression, pooled_macro_f1_non_regression, strict_pooled_improvement, equal_speaker_mean_ba_non_regression, tone_precision_drop_at_most_0.05, tone_recall_drop_at_most_0.05, tone_f1_drop_at_most_0.05, speaker_ba_drop_at_most_0.10.
Apply all nine conditions to the full panel; inspect complete metric differences for mixed, unchanged or worse behavior. Failure alone does not mean worse.

Speaker-bootstrap descriptive uncertainty from only 18 speakers, not population guarantees. Intervals including zero are suggestive, not demonstrated superiority. Bootstrap results do not alter the preregistered decision.

Source-declared NATIVE controls and LEARNER groups are secondary descriptive results; they do not replace the primary panel or infer status beyond source documentation.

Complete metrics, per-tone/support/confusions, paired categories, speaker differences, subgroups and decision checks follow (B minus A):

```json
{
  "schema_version": "experiment3-evaluation-v1",
  "panel": {
    "role": "PRIMARY_ALL_SEALED_ROWS",
    "rows": 720,
    "speakers": 18
  },
  "primary": {
    "A": {
      "correct_count": 381,
      "support": 720,
      "accuracy": 0.5291666666666667,
      "balanced_accuracy": 0.5291666666666667,
      "macro_f1": 0.5170396151839103,
      "per_tone": {
        "1": {
          "precision": 0.4976958525345622,
          "recall": 0.6,
          "f1": 0.5440806045340051,
          "support": 180
        },
        "2": {
          "precision": 0.6625,
          "recall": 0.29444444444444445,
          "f1": 0.4076923076923077,
          "support": 180
        },
        "3": {
          "precision": 0.5182186234817814,
          "recall": 0.7111111111111111,
          "f1": 0.5995316159250585,
          "support": 180
        },
        "4": {
          "precision": 0.5227272727272727,
          "recall": 0.5111111111111111,
          "f1": 0.5168539325842697,
          "support": 180
        }
      },
      "confusion_matrix": [
        [
          108,
          12,
          26,
          34
        ],
        [
          49,
          53,
          49,
          29
        ],
        [
          16,
          15,
          128,
          21
        ],
        [
          44,
          0,
          44,
          92
        ]
      ],
      "directed_confusions": {
        "T2->T3": {
          "count": 49,
          "denominator": 180,
          "rate": 0.2722222222222222
        },
        "T3->T2": {
          "count": 15,
          "denominator": 180,
          "rate": 0.08333333333333333
        },
        "T3->T4": {
          "count": 21,
          "denominator": 180,
          "rate": 0.11666666666666667
        },
        "T4->T3": {
          "count": 44,
          "denominator": 180,
          "rate": 0.24444444444444444
        }
      },
      "equal_speaker_mean_balanced_accuracy": 0.5291666666666667
    },
    "B": {
      "correct_count": 351,
      "support": 720,
      "accuracy": 0.4875,
      "balanced_accuracy": 0.4875,
      "macro_f1": 0.47563904637089943,
      "per_tone": {
        "1": {
          "precision": 0.3769968051118211,
          "recall": 0.6555555555555556,
          "f1": 0.4787018255578093,
          "support": 180
        },
        "2": {
          "precision": 0.6,
          "recall": 0.21666666666666667,
          "f1": 0.3183673469387755,
          "support": 180
        },
        "3": {
          "precision": 0.5523255813953488,
          "recall": 0.5277777777777778,
          "f1": 0.5397727272727273,
          "support": 180
        },
        "4": {
          "precision": 0.5823529411764706,
          "recall": 0.55,
          "f1": 0.5657142857142857,
          "support": 180
        }
      },
      "confusion_matrix": [
        [
          118,
          10,
          22,
          30
        ],
        [
          89,
          39,
          32,
          20
        ],
        [
          48,
          16,
          95,
          21
        ],
        [
          58,
          0,
          23,
          99
        ]
      ],
      "directed_confusions": {
        "T2->T3": {
          "count": 32,
          "denominator": 180,
          "rate": 0.17777777777777778
        },
        "T3->T2": {
          "count": 16,
          "denominator": 180,
          "rate": 0.08888888888888889
        },
        "T3->T4": {
          "count": 21,
          "denominator": 180,
          "rate": 0.11666666666666667
        },
        "T4->T3": {
          "count": 23,
          "denominator": 180,
          "rate": 0.12777777777777777
        }
      },
      "equal_speaker_mean_balanced_accuracy": 0.4875
    },
    "paired_correctness": {
      "both_correct": 292,
      "A_only_correct": 89,
      "B_only_correct": 59,
      "both_wrong": 280
    },
    "difference_B_minus_A": {
      "accuracy": -0.041666666666666664,
      "balanced_accuracy": -0.041666666666666664,
      "macro_f1": -0.041400568813010775,
      "per_tone": {
        "1": {
          "precision": -0.12069904742274112,
          "recall": 0.05555555555555555,
          "f1": -0.0653787789761957
        },
        "2": {
          "precision": -0.0625,
          "recall": -0.07777777777777778,
          "f1": -0.08932496075353218
        },
        "3": {
          "precision": 0.03410695791356746,
          "recall": -0.18333333333333332,
          "f1": -0.059758888652331275
        },
        "4": {
          "precision": 0.05962566844919786,
          "recall": 0.03888888888888889,
          "f1": 0.04886035313001605
        }
      },
      "equal_speaker_mean_balanced_accuracy": -0.041666666666666664
    }
  },
  "per_speaker": {
    "sait-ema:A_F001": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 28,
        "support": 40,
        "accuracy": 0.7,
        "balanced_accuracy": 0.7,
        "macro_f1": 0.6931216931216931,
        "per_tone": {
          "1": {
            "precision": 1.0,
            "recall": 0.8,
            "f1": 0.8888888888888888,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.4,
            "f1": 0.5714285714285714,
            "support": 10
          },
          "3": {
            "precision": 0.5882352941176471,
            "recall": 1.0,
            "f1": 0.7407407407407407,
            "support": 10
          },
          "4": {
            "precision": 0.5454545454545454,
            "recall": 0.6,
            "f1": 0.5714285714285714,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            8,
            0,
            0,
            2
          ],
          [
            0,
            4,
            3,
            3
          ],
          [
            0,
            0,
            10,
            0
          ],
          [
            0,
            0,
            4,
            6
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 4,
            "denominator": 10,
            "rate": 0.4
          }
        }
      },
      "B": {
        "correct_count": 20,
        "support": 40,
        "accuracy": 0.5,
        "balanced_accuracy": 0.5,
        "macro_f1": 0.45197947214076245,
        "per_tone": {
          "1": {
            "precision": 0.42857142857142855,
            "recall": 0.9,
            "f1": 0.5806451612903226,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.1,
            "f1": 0.18181818181818182,
            "support": 10
          },
          "3": {
            "precision": 0.5,
            "recall": 0.6,
            "f1": 0.5454545454545454,
            "support": 10
          },
          "4": {
            "precision": 0.6666666666666666,
            "recall": 0.4,
            "f1": 0.5,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            9,
            0,
            0,
            1
          ],
          [
            6,
            1,
            2,
            1
          ],
          [
            4,
            0,
            6,
            0
          ],
          [
            2,
            0,
            4,
            4
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 4,
            "denominator": 10,
            "rate": 0.4
          }
        }
      },
      "paired_correctness": {
        "both_correct": 19,
        "A_only_correct": 9,
        "B_only_correct": 1,
        "both_wrong": 11
      },
      "difference_B_minus_A": {
        "accuracy": -0.2,
        "balanced_accuracy": -0.2,
        "macro_f1": -0.24114222098093066,
        "per_tone": {
          "1": {
            "precision": -0.5714285714285714,
            "recall": 0.1,
            "f1": -0.30824372759856633
          },
          "2": {
            "precision": 0.0,
            "recall": -0.3,
            "f1": -0.38961038961038963
          },
          "3": {
            "precision": -0.08823529411764706,
            "recall": -0.4,
            "f1": -0.19528619528619529
          },
          "4": {
            "precision": 0.12121212121212122,
            "recall": -0.2,
            "f1": -0.07142857142857142
          }
        }
      }
    },
    "sait-ema:A_M001": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 25,
        "support": 40,
        "accuracy": 0.625,
        "balanced_accuracy": 0.625,
        "macro_f1": 0.5612207602339181,
        "per_tone": {
          "1": {
            "precision": 0.45454545454545453,
            "recall": 1.0,
            "f1": 0.625,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.8888888888888888,
            "recall": 0.8,
            "f1": 0.8421052631578947,
            "support": 10
          },
          "4": {
            "precision": 0.875,
            "recall": 0.7,
            "f1": 0.7777777777777778,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            10,
            0,
            0,
            0
          ],
          [
            9,
            0,
            0,
            1
          ],
          [
            1,
            1,
            8,
            0
          ],
          [
            2,
            0,
            1,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 25,
        "support": 40,
        "accuracy": 0.625,
        "balanced_accuracy": 0.625,
        "macro_f1": 0.6090812712704253,
        "per_tone": {
          "1": {
            "precision": 0.42857142857142855,
            "recall": 0.9,
            "f1": 0.5806451612903226,
            "support": 10
          },
          "2": {
            "precision": 0.6666666666666666,
            "recall": 0.2,
            "f1": 0.3076923076923077,
            "support": 10
          },
          "3": {
            "precision": 0.8571428571428571,
            "recall": 0.6,
            "f1": 0.7058823529411765,
            "support": 10
          },
          "4": {
            "precision": 0.8888888888888888,
            "recall": 0.8,
            "f1": 0.8421052631578947,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            9,
            0,
            1,
            0
          ],
          [
            8,
            2,
            0,
            0
          ],
          [
            2,
            1,
            6,
            1
          ],
          [
            2,
            0,
            0,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "paired_correctness": {
        "both_correct": 22,
        "A_only_correct": 3,
        "B_only_correct": 3,
        "both_wrong": 12
      },
      "difference_B_minus_A": {
        "accuracy": 0.0,
        "balanced_accuracy": 0.0,
        "macro_f1": 0.04786051103650724,
        "per_tone": {
          "1": {
            "precision": -0.025974025974025976,
            "recall": -0.1,
            "f1": -0.04435483870967742
          },
          "2": {
            "precision": 0.6666666666666666,
            "recall": 0.2,
            "f1": 0.3076923076923077
          },
          "3": {
            "precision": -0.031746031746031744,
            "recall": -0.2,
            "f1": -0.13622291021671826
          },
          "4": {
            "precision": 0.013888888888888888,
            "recall": 0.1,
            "f1": 0.06432748538011696
          }
        }
      }
    },
    "sait-ema:F001": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 23,
        "support": 40,
        "accuracy": 0.575,
        "balanced_accuracy": 0.575,
        "macro_f1": 0.5637973137973138,
        "per_tone": {
          "1": {
            "precision": 1.0,
            "recall": 0.3,
            "f1": 0.46153846153846156,
            "support": 10
          },
          "2": {
            "precision": 0.6363636363636364,
            "recall": 0.7,
            "f1": 0.6666666666666666,
            "support": 10
          },
          "3": {
            "precision": 0.625,
            "recall": 0.5,
            "f1": 0.5555555555555556,
            "support": 10
          },
          "4": {
            "precision": 0.4444444444444444,
            "recall": 0.8,
            "f1": 0.5714285714285714,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            3,
            3,
            1,
            3
          ],
          [
            0,
            7,
            0,
            3
          ],
          [
            0,
            1,
            5,
            4
          ],
          [
            0,
            0,
            2,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 4,
            "denominator": 10,
            "rate": 0.4
          },
          "T4->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          }
        }
      },
      "B": {
        "correct_count": 21,
        "support": 40,
        "accuracy": 0.525,
        "balanced_accuracy": 0.525,
        "macro_f1": 0.5303827751196172,
        "per_tone": {
          "1": {
            "precision": 0.3333333333333333,
            "recall": 0.4,
            "f1": 0.36363636363636365,
            "support": 10
          },
          "2": {
            "precision": 0.5555555555555556,
            "recall": 0.5,
            "f1": 0.5263157894736842,
            "support": 10
          },
          "3": {
            "precision": 0.6666666666666666,
            "recall": 0.6,
            "f1": 0.631578947368421,
            "support": 10
          },
          "4": {
            "precision": 0.6,
            "recall": 0.6,
            "f1": 0.6,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            4,
            4,
            0,
            2
          ],
          [
            5,
            5,
            0,
            0
          ],
          [
            2,
            0,
            6,
            2
          ],
          [
            1,
            0,
            3,
            6
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T4->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          }
        }
      },
      "paired_correctness": {
        "both_correct": 16,
        "A_only_correct": 7,
        "B_only_correct": 5,
        "both_wrong": 12
      },
      "difference_B_minus_A": {
        "accuracy": -0.05,
        "balanced_accuracy": -0.05,
        "macro_f1": -0.03341453867769657,
        "per_tone": {
          "1": {
            "precision": -0.6666666666666666,
            "recall": 0.1,
            "f1": -0.0979020979020979
          },
          "2": {
            "precision": -0.08080808080808081,
            "recall": -0.2,
            "f1": -0.14035087719298245
          },
          "3": {
            "precision": 0.041666666666666664,
            "recall": 0.1,
            "f1": 0.07602339181286549
          },
          "4": {
            "precision": 0.15555555555555556,
            "recall": -0.2,
            "f1": 0.02857142857142857
          }
        }
      }
    },
    "sait-ema:F002": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 18,
        "support": 40,
        "accuracy": 0.45,
        "balanced_accuracy": 0.45,
        "macro_f1": 0.4606786680189317,
        "per_tone": {
          "1": {
            "precision": 0.3157894736842105,
            "recall": 0.6,
            "f1": 0.41379310344827586,
            "support": 10
          },
          "2": {
            "precision": 0.375,
            "recall": 0.3,
            "f1": 0.3333333333333333,
            "support": 10
          },
          "3": {
            "precision": 0.5714285714285714,
            "recall": 0.4,
            "f1": 0.47058823529411764,
            "support": 10
          },
          "4": {
            "precision": 0.8333333333333334,
            "recall": 0.5,
            "f1": 0.625,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            2,
            2,
            0
          ],
          [
            6,
            3,
            1,
            0
          ],
          [
            2,
            3,
            4,
            1
          ],
          [
            5,
            0,
            0,
            5
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "B": {
        "correct_count": 17,
        "support": 40,
        "accuracy": 0.425,
        "balanced_accuracy": 0.425,
        "macro_f1": 0.3915966386554622,
        "per_tone": {
          "1": {
            "precision": 0.32,
            "recall": 0.8,
            "f1": 0.45714285714285713,
            "support": 10
          },
          "2": {
            "precision": 0.25,
            "recall": 0.1,
            "f1": 0.14285714285714285,
            "support": 10
          },
          "3": {
            "precision": 0.25,
            "recall": 0.1,
            "f1": 0.14285714285714285,
            "support": 10
          },
          "4": {
            "precision": 1.0,
            "recall": 0.7,
            "f1": 0.8235294117647058,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            8,
            0,
            2,
            0
          ],
          [
            8,
            1,
            1,
            0
          ],
          [
            6,
            3,
            1,
            0
          ],
          [
            3,
            0,
            0,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "paired_correctness": {
        "both_correct": 13,
        "A_only_correct": 5,
        "B_only_correct": 4,
        "both_wrong": 18
      },
      "difference_B_minus_A": {
        "accuracy": -0.025,
        "balanced_accuracy": -0.025,
        "macro_f1": -0.06908202936346952,
        "per_tone": {
          "1": {
            "precision": 0.004210526315789474,
            "recall": 0.2,
            "f1": 0.04334975369458128
          },
          "2": {
            "precision": -0.125,
            "recall": -0.2,
            "f1": -0.19047619047619047
          },
          "3": {
            "precision": -0.32142857142857145,
            "recall": -0.3,
            "f1": -0.3277310924369748
          },
          "4": {
            "precision": 0.16666666666666666,
            "recall": 0.2,
            "f1": 0.19852941176470587
          }
        }
      }
    },
    "sait-ema:F003": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 31,
        "support": 40,
        "accuracy": 0.775,
        "balanced_accuracy": 0.775,
        "macro_f1": 0.7630875316633831,
        "per_tone": {
          "1": {
            "precision": 0.7142857142857143,
            "recall": 0.5,
            "f1": 0.5882352941176471,
            "support": 10
          },
          "2": {
            "precision": 0.75,
            "recall": 0.9,
            "f1": 0.8181818181818182,
            "support": 10
          },
          "3": {
            "precision": 0.8333333333333334,
            "recall": 1.0,
            "f1": 0.9090909090909091,
            "support": 10
          },
          "4": {
            "precision": 0.7777777777777778,
            "recall": 0.7,
            "f1": 0.7368421052631579,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            5,
            3,
            1,
            1
          ],
          [
            0,
            9,
            0,
            1
          ],
          [
            0,
            0,
            10,
            0
          ],
          [
            2,
            0,
            1,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 30,
        "support": 40,
        "accuracy": 0.75,
        "balanced_accuracy": 0.75,
        "macro_f1": 0.7523477812177503,
        "per_tone": {
          "1": {
            "precision": 0.5714285714285714,
            "recall": 0.8,
            "f1": 0.6666666666666666,
            "support": 10
          },
          "2": {
            "precision": 0.8571428571428571,
            "recall": 0.6,
            "f1": 0.7058823529411765,
            "support": 10
          },
          "3": {
            "precision": 0.9,
            "recall": 0.9,
            "f1": 0.9,
            "support": 10
          },
          "4": {
            "precision": 0.7777777777777778,
            "recall": 0.7,
            "f1": 0.7368421052631579,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            8,
            1,
            1,
            0
          ],
          [
            3,
            6,
            0,
            1
          ],
          [
            0,
            0,
            9,
            1
          ],
          [
            3,
            0,
            0,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "paired_correctness": {
        "both_correct": 26,
        "A_only_correct": 5,
        "B_only_correct": 4,
        "both_wrong": 5
      },
      "difference_B_minus_A": {
        "accuracy": -0.025,
        "balanced_accuracy": -0.025,
        "macro_f1": -0.010739750445632799,
        "per_tone": {
          "1": {
            "precision": -0.14285714285714285,
            "recall": 0.3,
            "f1": 0.0784313725490196
          },
          "2": {
            "precision": 0.10714285714285714,
            "recall": -0.3,
            "f1": -0.11229946524064172
          },
          "3": {
            "precision": 0.06666666666666667,
            "recall": -0.1,
            "f1": -0.00909090909090909
          },
          "4": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
          }
        }
      }
    },
    "sait-ema:F004": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 24,
        "support": 40,
        "accuracy": 0.6,
        "balanced_accuracy": 0.6,
        "macro_f1": 0.6041189931350115,
        "per_tone": {
          "1": {
            "precision": 0.46153846153846156,
            "recall": 0.6,
            "f1": 0.5217391304347826,
            "support": 10
          },
          "2": {
            "precision": 0.6666666666666666,
            "recall": 0.6,
            "f1": 0.631578947368421,
            "support": 10
          },
          "3": {
            "precision": 0.6666666666666666,
            "recall": 0.6,
            "f1": 0.631578947368421,
            "support": 10
          },
          "4": {
            "precision": 0.6666666666666666,
            "recall": 0.6,
            "f1": 0.631578947368421,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            2,
            1,
            1
          ],
          [
            2,
            6,
            1,
            1
          ],
          [
            2,
            1,
            6,
            1
          ],
          [
            3,
            0,
            1,
            6
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 24,
        "support": 40,
        "accuracy": 0.6,
        "balanced_accuracy": 0.6,
        "macro_f1": 0.6005417956656347,
        "per_tone": {
          "1": {
            "precision": 0.42857142857142855,
            "recall": 0.6,
            "f1": 0.5,
            "support": 10
          },
          "2": {
            "precision": 0.5714285714285714,
            "recall": 0.4,
            "f1": 0.47058823529411764,
            "support": 10
          },
          "3": {
            "precision": 0.6666666666666666,
            "recall": 0.6,
            "f1": 0.631578947368421,
            "support": 10
          },
          "4": {
            "precision": 0.8,
            "recall": 0.8,
            "f1": 0.8,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            1,
            2,
            1
          ],
          [
            5,
            4,
            0,
            1
          ],
          [
            2,
            2,
            6,
            0
          ],
          [
            1,
            0,
            1,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 19,
        "A_only_correct": 5,
        "B_only_correct": 5,
        "both_wrong": 11
      },
      "difference_B_minus_A": {
        "accuracy": 0.0,
        "balanced_accuracy": 0.0,
        "macro_f1": -0.003577197469376767,
        "per_tone": {
          "1": {
            "precision": -0.03296703296703297,
            "recall": 0.0,
            "f1": -0.021739130434782608
          },
          "2": {
            "precision": -0.09523809523809523,
            "recall": -0.2,
            "f1": -0.1609907120743034
          },
          "3": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
          },
          "4": {
            "precision": 0.13333333333333333,
            "recall": 0.2,
            "f1": 0.16842105263157894
          }
        }
      }
    },
    "sait-ema:F005": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 18,
        "support": 40,
        "accuracy": 0.45,
        "balanced_accuracy": 0.45,
        "macro_f1": 0.444551282051282,
        "per_tone": {
          "1": {
            "precision": 1.0,
            "recall": 0.3,
            "f1": 0.46153846153846156,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.2,
            "f1": 0.3333333333333333,
            "support": 10
          },
          "3": {
            "precision": 0.3,
            "recall": 0.9,
            "f1": 0.45,
            "support": 10
          },
          "4": {
            "precision": 0.8,
            "recall": 0.4,
            "f1": 0.5333333333333333,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            3,
            0,
            7,
            0
          ],
          [
            0,
            2,
            8,
            0
          ],
          [
            0,
            0,
            9,
            1
          ],
          [
            0,
            0,
            6,
            4
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 8,
            "denominator": 10,
            "rate": 0.8
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 6,
            "denominator": 10,
            "rate": 0.6
          }
        }
      },
      "B": {
        "correct_count": 22,
        "support": 40,
        "accuracy": 0.55,
        "balanced_accuracy": 0.55,
        "macro_f1": 0.516089466089466,
        "per_tone": {
          "1": {
            "precision": 0.5454545454545454,
            "recall": 0.6,
            "f1": 0.5714285714285714,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.1,
            "f1": 0.18181818181818182,
            "support": 10
          },
          "3": {
            "precision": 0.4,
            "recall": 0.8,
            "f1": 0.5333333333333333,
            "support": 10
          },
          "4": {
            "precision": 0.875,
            "recall": 0.7,
            "f1": 0.7777777777777778,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            0,
            4,
            0
          ],
          [
            2,
            1,
            7,
            0
          ],
          [
            1,
            0,
            8,
            1
          ],
          [
            2,
            0,
            1,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 7,
            "denominator": 10,
            "rate": 0.7
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 16,
        "A_only_correct": 2,
        "B_only_correct": 6,
        "both_wrong": 16
      },
      "difference_B_minus_A": {
        "accuracy": 0.1,
        "balanced_accuracy": 0.1,
        "macro_f1": 0.07153818403818404,
        "per_tone": {
          "1": {
            "precision": -0.45454545454545453,
            "recall": 0.3,
            "f1": 0.10989010989010989
          },
          "2": {
            "precision": 0.0,
            "recall": -0.1,
            "f1": -0.15151515151515152
          },
          "3": {
            "precision": 0.1,
            "recall": -0.1,
            "f1": 0.08333333333333333
          },
          "4": {
            "precision": 0.075,
            "recall": 0.3,
            "f1": 0.24444444444444444
          }
        }
      }
    },
    "sait-ema:L_F001": {
      "source_declared_speaker_status": "LEARNER",
      "A": {
        "correct_count": 20,
        "support": 40,
        "accuracy": 0.5,
        "balanced_accuracy": 0.5,
        "macro_f1": 0.44,
        "per_tone": {
          "1": {
            "precision": 1.0,
            "recall": 0.5,
            "f1": 0.6666666666666666,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.4,
            "recall": 0.8,
            "f1": 0.5333333333333333,
            "support": 10
          },
          "4": {
            "precision": 0.4666666666666667,
            "recall": 0.7,
            "f1": 0.56,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            5,
            0,
            2,
            3
          ],
          [
            0,
            0,
            7,
            3
          ],
          [
            0,
            0,
            8,
            2
          ],
          [
            0,
            0,
            3,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 7,
            "denominator": 10,
            "rate": 0.7
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T4->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          }
        }
      },
      "B": {
        "correct_count": 19,
        "support": 40,
        "accuracy": 0.475,
        "balanced_accuracy": 0.475,
        "macro_f1": 0.4238834422657952,
        "per_tone": {
          "1": {
            "precision": 0.42857142857142855,
            "recall": 0.3,
            "f1": 0.35294117647058826,
            "support": 10
          },
          "2": {
            "precision": 0.5,
            "recall": 0.1,
            "f1": 0.16666666666666666,
            "support": 10
          },
          "3": {
            "precision": 0.5,
            "recall": 0.7,
            "f1": 0.5833333333333334,
            "support": 10
          },
          "4": {
            "precision": 0.47058823529411764,
            "recall": 0.8,
            "f1": 0.5925925925925926,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            3,
            1,
            4,
            2
          ],
          [
            1,
            1,
            3,
            5
          ],
          [
            1,
            0,
            7,
            2
          ],
          [
            2,
            0,
            0,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "paired_correctness": {
        "both_correct": 17,
        "A_only_correct": 3,
        "B_only_correct": 2,
        "both_wrong": 18
      },
      "difference_B_minus_A": {
        "accuracy": -0.025,
        "balanced_accuracy": -0.025,
        "macro_f1": -0.016116557734204794,
        "per_tone": {
          "1": {
            "precision": -0.5714285714285714,
            "recall": -0.2,
            "f1": -0.3137254901960784
          },
          "2": {
            "precision": 0.5,
            "recall": 0.1,
            "f1": 0.16666666666666666
          },
          "3": {
            "precision": 0.1,
            "recall": -0.1,
            "f1": 0.05
          },
          "4": {
            "precision": 0.00392156862745098,
            "recall": 0.1,
            "f1": 0.03259259259259259
          }
        }
      }
    },
    "sait-ema:L_F002": {
      "source_declared_speaker_status": "LEARNER",
      "A": {
        "correct_count": 20,
        "support": 40,
        "accuracy": 0.5,
        "balanced_accuracy": 0.5,
        "macro_f1": 0.4991360089186176,
        "per_tone": {
          "1": {
            "precision": 0.6666666666666666,
            "recall": 0.4,
            "f1": 0.5,
            "support": 10
          },
          "2": {
            "precision": 0.8,
            "recall": 0.4,
            "f1": 0.5333333333333333,
            "support": 10
          },
          "3": {
            "precision": 0.5,
            "recall": 0.8,
            "f1": 0.6153846153846154,
            "support": 10
          },
          "4": {
            "precision": 0.3076923076923077,
            "recall": 0.4,
            "f1": 0.34782608695652173,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            4,
            1,
            2,
            3
          ],
          [
            1,
            4,
            1,
            4
          ],
          [
            0,
            0,
            8,
            2
          ],
          [
            1,
            0,
            5,
            4
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T4->T3": {
            "count": 5,
            "denominator": 10,
            "rate": 0.5
          }
        }
      },
      "B": {
        "correct_count": 16,
        "support": 40,
        "accuracy": 0.4,
        "balanced_accuracy": 0.4,
        "macro_f1": 0.3932973459289249,
        "per_tone": {
          "1": {
            "precision": 0.3,
            "recall": 0.6,
            "f1": 0.4,
            "support": 10
          },
          "2": {
            "precision": 0.6666666666666666,
            "recall": 0.2,
            "f1": 0.3076923076923077,
            "support": 10
          },
          "3": {
            "precision": 0.4444444444444444,
            "recall": 0.4,
            "f1": 0.42105263157894735,
            "support": 10
          },
          "4": {
            "precision": 0.5,
            "recall": 0.4,
            "f1": 0.4444444444444444,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            1,
            2,
            1
          ],
          [
            7,
            2,
            0,
            1
          ],
          [
            4,
            0,
            4,
            2
          ],
          [
            3,
            0,
            3,
            4
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T4->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          }
        }
      },
      "paired_correctness": {
        "both_correct": 14,
        "A_only_correct": 6,
        "B_only_correct": 2,
        "both_wrong": 18
      },
      "difference_B_minus_A": {
        "accuracy": -0.1,
        "balanced_accuracy": -0.1,
        "macro_f1": -0.10583866298969274,
        "per_tone": {
          "1": {
            "precision": -0.36666666666666664,
            "recall": 0.2,
            "f1": -0.1
          },
          "2": {
            "precision": -0.13333333333333333,
            "recall": -0.2,
            "f1": -0.22564102564102564
          },
          "3": {
            "precision": -0.05555555555555555,
            "recall": -0.4,
            "f1": -0.19433198380566802
          },
          "4": {
            "precision": 0.19230769230769232,
            "recall": 0.0,
            "f1": 0.0966183574879227
          }
        }
      }
    },
    "sait-ema:L_F003": {
      "source_declared_speaker_status": "LEARNER",
      "A": {
        "correct_count": 28,
        "support": 40,
        "accuracy": 0.7,
        "balanced_accuracy": 0.7,
        "macro_f1": 0.6842373312961548,
        "per_tone": {
          "1": {
            "precision": 0.5294117647058824,
            "recall": 0.9,
            "f1": 0.6666666666666666,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.7,
            "f1": 0.8235294117647058,
            "support": 10
          },
          "3": {
            "precision": 0.75,
            "recall": 0.9,
            "f1": 0.8181818181818182,
            "support": 10
          },
          "4": {
            "precision": 0.75,
            "recall": 0.3,
            "f1": 0.42857142857142855,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            9,
            0,
            0,
            1
          ],
          [
            1,
            7,
            2,
            0
          ],
          [
            1,
            0,
            9,
            0
          ],
          [
            6,
            0,
            1,
            3
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 21,
        "support": 40,
        "accuracy": 0.525,
        "balanced_accuracy": 0.525,
        "macro_f1": 0.4697802197802198,
        "per_tone": {
          "1": {
            "precision": 0.4444444444444444,
            "recall": 0.8,
            "f1": 0.5714285714285714,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.2,
            "f1": 0.3333333333333333,
            "support": 10
          },
          "3": {
            "precision": 0.5294117647058824,
            "recall": 0.9,
            "f1": 0.6666666666666666,
            "support": 10
          },
          "4": {
            "precision": 0.6666666666666666,
            "recall": 0.2,
            "f1": 0.3076923076923077,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            8,
            0,
            1,
            1
          ],
          [
            1,
            2,
            7,
            0
          ],
          [
            1,
            0,
            9,
            0
          ],
          [
            8,
            0,
            0,
            2
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 7,
            "denominator": 10,
            "rate": 0.7
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "paired_correctness": {
        "both_correct": 21,
        "A_only_correct": 7,
        "B_only_correct": 0,
        "both_wrong": 12
      },
      "difference_B_minus_A": {
        "accuracy": -0.175,
        "balanced_accuracy": -0.175,
        "macro_f1": -0.21445711151593505,
        "per_tone": {
          "1": {
            "precision": -0.08496732026143791,
            "recall": -0.1,
            "f1": -0.09523809523809523
          },
          "2": {
            "precision": 0.0,
            "recall": -0.5,
            "f1": -0.49019607843137253
          },
          "3": {
            "precision": -0.22058823529411764,
            "recall": 0.0,
            "f1": -0.15151515151515152
          },
          "4": {
            "precision": -0.08333333333333333,
            "recall": -0.1,
            "f1": -0.12087912087912088
          }
        }
      }
    },
    "sait-ema:L_M001": {
      "source_declared_speaker_status": "LEARNER",
      "A": {
        "correct_count": 27,
        "support": 40,
        "accuracy": 0.675,
        "balanced_accuracy": 0.675,
        "macro_f1": 0.6773755656108598,
        "per_tone": {
          "1": {
            "precision": 0.8571428571428571,
            "recall": 0.6,
            "f1": 0.7058823529411765,
            "support": 10
          },
          "2": {
            "precision": 0.7142857142857143,
            "recall": 0.5,
            "f1": 0.5882352941176471,
            "support": 10
          },
          "3": {
            "precision": 0.8,
            "recall": 0.8,
            "f1": 0.8,
            "support": 10
          },
          "4": {
            "precision": 0.5,
            "recall": 0.8,
            "f1": 0.6153846153846154,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            0,
            0,
            4
          ],
          [
            0,
            5,
            1,
            4
          ],
          [
            0,
            2,
            8,
            0
          ],
          [
            1,
            0,
            1,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 27,
        "support": 40,
        "accuracy": 0.675,
        "balanced_accuracy": 0.675,
        "macro_f1": 0.6774513008864873,
        "per_tone": {
          "1": {
            "precision": 0.5454545454545454,
            "recall": 0.6,
            "f1": 0.5714285714285714,
            "support": 10
          },
          "2": {
            "precision": 0.8571428571428571,
            "recall": 0.6,
            "f1": 0.7058823529411765,
            "support": 10
          },
          "3": {
            "precision": 0.7777777777777778,
            "recall": 0.7,
            "f1": 0.7368421052631579,
            "support": 10
          },
          "4": {
            "precision": 0.6153846153846154,
            "recall": 0.8,
            "f1": 0.6956521739130435,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            0,
            0,
            4
          ],
          [
            2,
            6,
            1,
            1
          ],
          [
            2,
            1,
            7,
            0
          ],
          [
            1,
            0,
            1,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 25,
        "A_only_correct": 2,
        "B_only_correct": 2,
        "both_wrong": 11
      },
      "difference_B_minus_A": {
        "accuracy": 0.0,
        "balanced_accuracy": 0.0,
        "macro_f1": 7.573527562758954e-05,
        "per_tone": {
          "1": {
            "precision": -0.3116883116883117,
            "recall": 0.0,
            "f1": -0.13445378151260504
          },
          "2": {
            "precision": 0.14285714285714285,
            "recall": 0.1,
            "f1": 0.11764705882352941
          },
          "3": {
            "precision": -0.022222222222222223,
            "recall": -0.1,
            "f1": -0.06315789473684211
          },
          "4": {
            "precision": 0.11538461538461539,
            "recall": 0.0,
            "f1": 0.0802675585284281
          }
        }
      }
    },
    "sait-ema:L_M002": {
      "source_declared_speaker_status": "LEARNER",
      "A": {
        "correct_count": 17,
        "support": 40,
        "accuracy": 0.425,
        "balanced_accuracy": 0.425,
        "macro_f1": 0.36878306878306877,
        "per_tone": {
          "1": {
            "precision": 0.8,
            "recall": 0.4,
            "f1": 0.5333333333333333,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.29411764705882354,
            "recall": 0.5,
            "f1": 0.37037037037037035,
            "support": 10
          },
          "4": {
            "precision": 0.4444444444444444,
            "recall": 0.8,
            "f1": 0.5714285714285714,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            4,
            0,
            3,
            3
          ],
          [
            0,
            0,
            8,
            2
          ],
          [
            0,
            0,
            5,
            5
          ],
          [
            1,
            0,
            1,
            8
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 8,
            "denominator": 10,
            "rate": 0.8
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 5,
            "denominator": 10,
            "rate": 0.5
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 12,
        "support": 40,
        "accuracy": 0.3,
        "balanced_accuracy": 0.3,
        "macro_f1": 0.25757575757575757,
        "per_tone": {
          "1": {
            "precision": 0.35294117647058826,
            "recall": 0.6,
            "f1": 0.4444444444444444,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.25,
            "recall": 0.2,
            "f1": 0.2222222222222222,
            "support": 10
          },
          "4": {
            "precision": 0.3333333333333333,
            "recall": 0.4,
            "f1": 0.36363636363636365,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            1,
            0,
            3
          ],
          [
            3,
            0,
            5,
            2
          ],
          [
            3,
            2,
            2,
            3
          ],
          [
            5,
            0,
            1,
            4
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 5,
            "denominator": 10,
            "rate": 0.5
          },
          "T3->T2": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T4": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 9,
        "A_only_correct": 8,
        "B_only_correct": 3,
        "both_wrong": 20
      },
      "difference_B_minus_A": {
        "accuracy": -0.125,
        "balanced_accuracy": -0.125,
        "macro_f1": -0.11120731120731121,
        "per_tone": {
          "1": {
            "precision": -0.4470588235294118,
            "recall": 0.2,
            "f1": -0.08888888888888889
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
          },
          "3": {
            "precision": -0.04411764705882353,
            "recall": -0.3,
            "f1": -0.14814814814814814
          },
          "4": {
            "precision": -0.1111111111111111,
            "recall": -0.4,
            "f1": -0.2077922077922078
          }
        }
      }
    },
    "sait-ema:L_M003": {
      "source_declared_speaker_status": "LEARNER",
      "A": {
        "correct_count": 8,
        "support": 40,
        "accuracy": 0.2,
        "balanced_accuracy": 0.2,
        "macro_f1": 0.17007168458781363,
        "per_tone": {
          "1": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "2": {
            "precision": 0.25,
            "recall": 0.2,
            "f1": 0.2222222222222222,
            "support": 10
          },
          "3": {
            "precision": 0.19047619047619047,
            "recall": 0.4,
            "f1": 0.25806451612903225,
            "support": 10
          },
          "4": {
            "precision": 0.2,
            "recall": 0.2,
            "f1": 0.2,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            0,
            1,
            2,
            7
          ],
          [
            0,
            2,
            7,
            1
          ],
          [
            1,
            5,
            4,
            0
          ],
          [
            0,
            0,
            8,
            2
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 7,
            "denominator": 10,
            "rate": 0.7
          },
          "T3->T2": {
            "count": 5,
            "denominator": 10,
            "rate": 0.5
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 8,
            "denominator": 10,
            "rate": 0.8
          }
        }
      },
      "B": {
        "correct_count": 11,
        "support": 40,
        "accuracy": 0.275,
        "balanced_accuracy": 0.275,
        "macro_f1": 0.26925049195879724,
        "per_tone": {
          "1": {
            "precision": 0.18181818181818182,
            "recall": 0.2,
            "f1": 0.19047619047619047,
            "support": 10
          },
          "2": {
            "precision": 0.4444444444444444,
            "recall": 0.4,
            "f1": 0.42105263157894735,
            "support": 10
          },
          "3": {
            "precision": 0.14285714285714285,
            "recall": 0.1,
            "f1": 0.11764705882352941,
            "support": 10
          },
          "4": {
            "precision": 0.3076923076923077,
            "recall": 0.4,
            "f1": 0.34782608695652173,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            2,
            0,
            0,
            8
          ],
          [
            3,
            4,
            2,
            1
          ],
          [
            4,
            5,
            1,
            0
          ],
          [
            2,
            0,
            4,
            4
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T2": {
            "count": 5,
            "denominator": 10,
            "rate": 0.5
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 4,
            "denominator": 10,
            "rate": 0.4
          }
        }
      },
      "paired_correctness": {
        "both_correct": 4,
        "A_only_correct": 4,
        "B_only_correct": 7,
        "both_wrong": 25
      },
      "difference_B_minus_A": {
        "accuracy": 0.075,
        "balanced_accuracy": 0.075,
        "macro_f1": 0.09917880737098363,
        "per_tone": {
          "1": {
            "precision": 0.18181818181818182,
            "recall": 0.2,
            "f1": 0.19047619047619047
          },
          "2": {
            "precision": 0.19444444444444445,
            "recall": 0.2,
            "f1": 0.19883040935672514
          },
          "3": {
            "precision": -0.047619047619047616,
            "recall": -0.3,
            "f1": -0.14041745730550284
          },
          "4": {
            "precision": 0.1076923076923077,
            "recall": 0.2,
            "f1": 0.14782608695652175
          }
        }
      }
    },
    "sait-ema:M001": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 19,
        "support": 40,
        "accuracy": 0.475,
        "balanced_accuracy": 0.475,
        "macro_f1": 0.40051975051975053,
        "per_tone": {
          "1": {
            "precision": 0.37037037037037035,
            "recall": 1.0,
            "f1": 0.5405405405405406,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.6,
            "recall": 0.6,
            "f1": 0.6,
            "support": 10
          },
          "4": {
            "precision": 1.0,
            "recall": 0.3,
            "f1": 0.46153846153846156,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            10,
            0,
            0,
            0
          ],
          [
            8,
            0,
            2,
            0
          ],
          [
            4,
            0,
            6,
            0
          ],
          [
            5,
            0,
            2,
            3
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          }
        }
      },
      "B": {
        "correct_count": 16,
        "support": 40,
        "accuracy": 0.4,
        "balanced_accuracy": 0.4,
        "macro_f1": 0.346996996996997,
        "per_tone": {
          "1": {
            "precision": 0.2962962962962963,
            "recall": 0.8,
            "f1": 0.43243243243243246,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.6,
            "recall": 0.3,
            "f1": 0.4,
            "support": 10
          },
          "4": {
            "precision": 0.625,
            "recall": 0.5,
            "f1": 0.5555555555555556,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            8,
            0,
            1,
            1
          ],
          [
            8,
            0,
            1,
            1
          ],
          [
            6,
            0,
            3,
            1
          ],
          [
            5,
            0,
            0,
            5
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          }
        }
      },
      "paired_correctness": {
        "both_correct": 14,
        "A_only_correct": 5,
        "B_only_correct": 2,
        "both_wrong": 19
      },
      "difference_B_minus_A": {
        "accuracy": -0.075,
        "balanced_accuracy": -0.075,
        "macro_f1": -0.05352275352275352,
        "per_tone": {
          "1": {
            "precision": -0.07407407407407407,
            "recall": -0.2,
            "f1": -0.10810810810810811
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
          },
          "3": {
            "precision": 0.0,
            "recall": -0.3,
            "f1": -0.2
          },
          "4": {
            "precision": -0.375,
            "recall": 0.2,
            "f1": 0.09401709401709402
          }
        }
      }
    },
    "sait-ema:M002": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 21,
        "support": 40,
        "accuracy": 0.525,
        "balanced_accuracy": 0.525,
        "macro_f1": 0.44886363636363635,
        "per_tone": {
          "1": {
            "precision": 0.42857142857142855,
            "recall": 0.6,
            "f1": 0.5,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.6428571428571429,
            "recall": 0.9,
            "f1": 0.75,
            "support": 10
          },
          "4": {
            "precision": 0.5,
            "recall": 0.6,
            "f1": 0.5454545454545454,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            6,
            0,
            1,
            3
          ],
          [
            5,
            0,
            3,
            2
          ],
          [
            0,
            0,
            9,
            1
          ],
          [
            3,
            0,
            1,
            6
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 15,
        "support": 40,
        "accuracy": 0.375,
        "balanced_accuracy": 0.375,
        "macro_f1": 0.3277527902715309,
        "per_tone": {
          "1": {
            "precision": 0.2631578947368421,
            "recall": 0.5,
            "f1": 0.3448275862068966,
            "support": 10
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          },
          "3": {
            "precision": 0.5,
            "recall": 0.4,
            "f1": 0.4444444444444444,
            "support": 10
          },
          "4": {
            "precision": 0.46153846153846156,
            "recall": 0.6,
            "f1": 0.5217391304347826,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            5,
            0,
            2,
            3
          ],
          [
            8,
            0,
            1,
            1
          ],
          [
            3,
            0,
            4,
            3
          ],
          [
            3,
            0,
            1,
            6
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 14,
        "A_only_correct": 7,
        "B_only_correct": 1,
        "both_wrong": 18
      },
      "difference_B_minus_A": {
        "accuracy": -0.15,
        "balanced_accuracy": -0.15,
        "macro_f1": -0.12111084609210546,
        "per_tone": {
          "1": {
            "precision": -0.16541353383458646,
            "recall": -0.1,
            "f1": -0.15517241379310345
          },
          "2": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0
          },
          "3": {
            "precision": -0.14285714285714285,
            "recall": -0.5,
            "f1": -0.3055555555555556
          },
          "4": {
            "precision": -0.038461538461538464,
            "recall": 0.0,
            "f1": -0.023715415019762844
          }
        }
      }
    },
    "sait-ema:M003": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 18,
        "support": 40,
        "accuracy": 0.45,
        "balanced_accuracy": 0.45,
        "macro_f1": 0.40468960863697706,
        "per_tone": {
          "1": {
            "precision": 0.34615384615384615,
            "recall": 0.9,
            "f1": 0.5,
            "support": 10
          },
          "2": {
            "precision": 0.3333333333333333,
            "recall": 0.1,
            "f1": 0.15384615384615385,
            "support": 10
          },
          "3": {
            "precision": 0.6666666666666666,
            "recall": 0.6,
            "f1": 0.631578947368421,
            "support": 10
          },
          "4": {
            "precision": 1.0,
            "recall": 0.2,
            "f1": 0.3333333333333333,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            9,
            0,
            1,
            0
          ],
          [
            9,
            1,
            0,
            0
          ],
          [
            2,
            2,
            6,
            0
          ],
          [
            6,
            0,
            2,
            2
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          }
        }
      },
      "B": {
        "correct_count": 20,
        "support": 40,
        "accuracy": 0.5,
        "balanced_accuracy": 0.5,
        "macro_f1": 0.4793040293040293,
        "per_tone": {
          "1": {
            "precision": 0.36,
            "recall": 0.9,
            "f1": 0.5142857142857142,
            "support": 10
          },
          "2": {
            "precision": 0.6666666666666666,
            "recall": 0.2,
            "f1": 0.3076923076923077,
            "support": 10
          },
          "3": {
            "precision": 0.75,
            "recall": 0.6,
            "f1": 0.6666666666666666,
            "support": 10
          },
          "4": {
            "precision": 0.75,
            "recall": 0.3,
            "f1": 0.42857142857142855,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            9,
            1,
            0,
            0
          ],
          [
            7,
            2,
            0,
            1
          ],
          [
            4,
            0,
            6,
            0
          ],
          [
            5,
            0,
            2,
            3
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T4->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          }
        }
      },
      "paired_correctness": {
        "both_correct": 14,
        "A_only_correct": 4,
        "B_only_correct": 6,
        "both_wrong": 16
      },
      "difference_B_minus_A": {
        "accuracy": 0.05,
        "balanced_accuracy": 0.05,
        "macro_f1": 0.07461442066705225,
        "per_tone": {
          "1": {
            "precision": 0.013846153846153847,
            "recall": 0.0,
            "f1": 0.014285714285714285
          },
          "2": {
            "precision": 0.3333333333333333,
            "recall": 0.1,
            "f1": 0.15384615384615385
          },
          "3": {
            "precision": 0.08333333333333333,
            "recall": 0.0,
            "f1": 0.03508771929824561
          },
          "4": {
            "precision": -0.25,
            "recall": 0.1,
            "f1": 0.09523809523809523
          }
        }
      }
    },
    "sait-ema:M004": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 14,
        "support": 40,
        "accuracy": 0.35,
        "balanced_accuracy": 0.35,
        "macro_f1": 0.27904040404040403,
        "per_tone": {
          "1": {
            "precision": 0.2692307692307692,
            "recall": 0.7,
            "f1": 0.3888888888888889,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.1,
            "f1": 0.18181818181818182,
            "support": 10
          },
          "3": {
            "precision": 0.5,
            "recall": 0.6,
            "f1": 0.5454545454545454,
            "support": 10
          },
          "4": {
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            7,
            0,
            3,
            0
          ],
          [
            7,
            1,
            2,
            0
          ],
          [
            3,
            0,
            6,
            1
          ],
          [
            9,
            0,
            1,
            0
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "B": {
        "correct_count": 16,
        "support": 40,
        "accuracy": 0.4,
        "balanced_accuracy": 0.4,
        "macro_f1": 0.34527972027972026,
        "per_tone": {
          "1": {
            "precision": 0.30434782608695654,
            "recall": 0.7,
            "f1": 0.42424242424242425,
            "support": 10
          },
          "2": {
            "precision": 0.5,
            "recall": 0.1,
            "f1": 0.16666666666666666,
            "support": 10
          },
          "3": {
            "precision": 0.5833333333333334,
            "recall": 0.7,
            "f1": 0.6363636363636364,
            "support": 10
          },
          "4": {
            "precision": 0.3333333333333333,
            "recall": 0.1,
            "f1": 0.15384615384615385,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            7,
            0,
            2,
            1
          ],
          [
            7,
            1,
            2,
            0
          ],
          [
            1,
            1,
            7,
            1
          ],
          [
            8,
            0,
            1,
            1
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 2,
            "denominator": 10,
            "rate": 0.2
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 13,
        "A_only_correct": 1,
        "B_only_correct": 3,
        "both_wrong": 23
      },
      "difference_B_minus_A": {
        "accuracy": 0.05,
        "balanced_accuracy": 0.05,
        "macro_f1": 0.06623931623931624,
        "per_tone": {
          "1": {
            "precision": 0.03511705685618729,
            "recall": 0.0,
            "f1": 0.03535353535353535
          },
          "2": {
            "precision": -0.5,
            "recall": 0.0,
            "f1": -0.015151515151515152
          },
          "3": {
            "precision": 0.08333333333333333,
            "recall": 0.1,
            "f1": 0.09090909090909091
          },
          "4": {
            "precision": 0.3333333333333333,
            "recall": 0.1,
            "f1": 0.15384615384615385
          }
        }
      }
    },
    "sait-ema:M005": {
      "source_declared_speaker_status": "NATIVE",
      "A": {
        "correct_count": 22,
        "support": 40,
        "accuracy": 0.55,
        "balanced_accuracy": 0.55,
        "macro_f1": 0.5389957264957265,
        "per_tone": {
          "1": {
            "precision": 0.875,
            "recall": 0.7,
            "f1": 0.7777777777777778,
            "support": 10
          },
          "2": {
            "precision": 1.0,
            "recall": 0.2,
            "f1": 0.3333333333333333,
            "support": 10
          },
          "3": {
            "precision": 0.5,
            "recall": 0.7,
            "f1": 0.5833333333333334,
            "support": 10
          },
          "4": {
            "precision": 0.375,
            "recall": 0.6,
            "f1": 0.46153846153846156,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            7,
            0,
            0,
            3
          ],
          [
            1,
            2,
            3,
            4
          ],
          [
            0,
            0,
            7,
            3
          ],
          [
            0,
            0,
            4,
            6
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T3->T2": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T4": {
            "count": 3,
            "denominator": 10,
            "rate": 0.3
          },
          "T4->T3": {
            "count": 4,
            "denominator": 10,
            "rate": 0.4
          }
        }
      },
      "B": {
        "correct_count": 19,
        "support": 40,
        "accuracy": 0.475,
        "balanced_accuracy": 0.475,
        "macro_f1": 0.42658730158730157,
        "per_tone": {
          "1": {
            "precision": 0.47058823529411764,
            "recall": 0.8,
            "f1": 0.5925925925925926,
            "support": 10
          },
          "2": {
            "precision": 0.5,
            "recall": 0.1,
            "f1": 0.16666666666666666,
            "support": 10
          },
          "3": {
            "precision": 0.75,
            "recall": 0.3,
            "f1": 0.42857142857142855,
            "support": 10
          },
          "4": {
            "precision": 0.4117647058823529,
            "recall": 0.7,
            "f1": 0.5185185185185185,
            "support": 10
          }
        },
        "confusion_matrix": [
          [
            8,
            0,
            0,
            2
          ],
          [
            5,
            1,
            0,
            4
          ],
          [
            2,
            1,
            3,
            4
          ],
          [
            2,
            0,
            1,
            7
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 0,
            "denominator": 10,
            "rate": 0.0
          },
          "T3->T2": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          },
          "T3->T4": {
            "count": 4,
            "denominator": 10,
            "rate": 0.4
          },
          "T4->T3": {
            "count": 1,
            "denominator": 10,
            "rate": 0.1
          }
        }
      },
      "paired_correctness": {
        "both_correct": 16,
        "A_only_correct": 6,
        "B_only_correct": 3,
        "both_wrong": 15
      },
      "difference_B_minus_A": {
        "accuracy": -0.075,
        "balanced_accuracy": -0.075,
        "macro_f1": -0.11240842490842491,
        "per_tone": {
          "1": {
            "precision": -0.40441176470588236,
            "recall": 0.1,
            "f1": -0.18518518518518517
          },
          "2": {
            "precision": -0.5,
            "recall": -0.1,
            "f1": -0.16666666666666666
          },
          "3": {
            "precision": 0.25,
            "recall": -0.4,
            "f1": -0.15476190476190477
          },
          "4": {
            "precision": 0.03676470588235294,
            "recall": 0.1,
            "f1": 0.05698005698005698
          }
        }
      }
    }
  },
  "source_declared_status_subgroups": {
    "LEARNER": {
      "role": "SECONDARY_DESCRIPTIVE",
      "speaker_count": 6,
      "A": {
        "correct_count": 120,
        "support": 240,
        "accuracy": 0.5,
        "balanced_accuracy": 0.5,
        "macro_f1": 0.4943245806871216,
        "per_tone": {
          "1": {
            "precision": 0.6829268292682927,
            "recall": 0.4666666666666667,
            "f1": 0.5544554455445545,
            "support": 60
          },
          "2": {
            "precision": 0.6666666666666666,
            "recall": 0.3,
            "f1": 0.41379310344827586,
            "support": 60
          },
          "3": {
            "precision": 0.4375,
            "recall": 0.7,
            "f1": 0.5384615384615384,
            "support": 60
          },
          "4": {
            "precision": 0.42105263157894735,
            "recall": 0.5333333333333333,
            "f1": 0.47058823529411764,
            "support": 60
          }
        },
        "confusion_matrix": [
          [
            28,
            2,
            9,
            21
          ],
          [
            2,
            18,
            26,
            14
          ],
          [
            2,
            7,
            42,
            9
          ],
          [
            9,
            0,
            19,
            32
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 26,
            "denominator": 60,
            "rate": 0.43333333333333335
          },
          "T3->T2": {
            "count": 7,
            "denominator": 60,
            "rate": 0.11666666666666667
          },
          "T3->T4": {
            "count": 9,
            "denominator": 60,
            "rate": 0.15
          },
          "T4->T3": {
            "count": 19,
            "denominator": 60,
            "rate": 0.31666666666666665
          }
        }
      },
      "B": {
        "correct_count": 106,
        "support": 240,
        "accuracy": 0.44166666666666665,
        "balanced_accuracy": 0.44166666666666665,
        "macro_f1": 0.4348635521975732,
        "per_tone": {
          "1": {
            "precision": 0.36904761904761907,
            "recall": 0.5166666666666667,
            "f1": 0.4305555555555556,
            "support": 60
          },
          "2": {
            "precision": 0.5769230769230769,
            "recall": 0.25,
            "f1": 0.3488372093023256,
            "support": 60
          },
          "3": {
            "precision": 0.46875,
            "recall": 0.5,
            "f1": 0.4838709677419355,
            "support": 60
          },
          "4": {
            "precision": 0.45454545454545453,
            "recall": 0.5,
            "f1": 0.47619047619047616,
            "support": 60
          }
        },
        "confusion_matrix": [
          [
            31,
            3,
            7,
            19
          ],
          [
            17,
            15,
            18,
            10
          ],
          [
            15,
            8,
            30,
            7
          ],
          [
            21,
            0,
            9,
            30
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 18,
            "denominator": 60,
            "rate": 0.3
          },
          "T3->T2": {
            "count": 8,
            "denominator": 60,
            "rate": 0.13333333333333333
          },
          "T3->T4": {
            "count": 7,
            "denominator": 60,
            "rate": 0.11666666666666667
          },
          "T4->T3": {
            "count": 9,
            "denominator": 60,
            "rate": 0.15
          }
        }
      },
      "paired_correctness": {
        "both_correct": 90,
        "A_only_correct": 30,
        "B_only_correct": 16,
        "both_wrong": 104
      },
      "difference_B_minus_A": {
        "accuracy": -0.058333333333333334,
        "balanced_accuracy": -0.058333333333333334,
        "macro_f1": -0.0594610284895484,
        "per_tone": {
          "1": {
            "precision": -0.3138792102206736,
            "recall": 0.05,
            "f1": -0.1238998899889989
          },
          "2": {
            "precision": -0.08974358974358974,
            "recall": -0.05,
            "f1": -0.06495589414595028
          },
          "3": {
            "precision": 0.03125,
            "recall": -0.2,
            "f1": -0.05459057071960298
          },
          "4": {
            "precision": 0.03349282296650718,
            "recall": -0.03333333333333333,
            "f1": 0.0056022408963585435
          }
        }
      }
    },
    "NATIVE": {
      "role": "SECONDARY_DESCRIPTIVE",
      "speaker_count": 12,
      "A": {
        "correct_count": 261,
        "support": 480,
        "accuracy": 0.54375,
        "balanced_accuracy": 0.54375,
        "macro_f1": 0.5313264275788006,
        "per_tone": {
          "1": {
            "precision": 0.45454545454545453,
            "recall": 0.6666666666666666,
            "f1": 0.5405405405405406,
            "support": 120
          },
          "2": {
            "precision": 0.660377358490566,
            "recall": 0.2916666666666667,
            "f1": 0.4046242774566474,
            "support": 120
          },
          "3": {
            "precision": 0.5695364238410596,
            "recall": 0.7166666666666667,
            "f1": 0.6346863468634686,
            "support": 120
          },
          "4": {
            "precision": 0.6,
            "recall": 0.5,
            "f1": 0.5454545454545454,
            "support": 120
          }
        },
        "confusion_matrix": [
          [
            80,
            10,
            17,
            13
          ],
          [
            47,
            35,
            23,
            15
          ],
          [
            14,
            8,
            86,
            12
          ],
          [
            35,
            0,
            25,
            60
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 23,
            "denominator": 120,
            "rate": 0.19166666666666668
          },
          "T3->T2": {
            "count": 8,
            "denominator": 120,
            "rate": 0.06666666666666667
          },
          "T3->T4": {
            "count": 12,
            "denominator": 120,
            "rate": 0.1
          },
          "T4->T3": {
            "count": 25,
            "denominator": 120,
            "rate": 0.20833333333333334
          }
        }
      },
      "B": {
        "correct_count": 245,
        "support": 480,
        "accuracy": 0.5104166666666666,
        "balanced_accuracy": 0.5104166666666666,
        "macro_f1": 0.49667524871607577,
        "per_tone": {
          "1": {
            "precision": 0.3799126637554585,
            "recall": 0.725,
            "f1": 0.498567335243553,
            "support": 120
          },
          "2": {
            "precision": 0.6153846153846154,
            "recall": 0.2,
            "f1": 0.3018867924528302,
            "support": 120
          },
          "3": {
            "precision": 0.6018518518518519,
            "recall": 0.5416666666666666,
            "f1": 0.5701754385964912,
            "support": 120
          },
          "4": {
            "precision": 0.6634615384615384,
            "recall": 0.575,
            "f1": 0.6160714285714286,
            "support": 120
          }
        },
        "confusion_matrix": [
          [
            87,
            7,
            15,
            11
          ],
          [
            72,
            24,
            14,
            10
          ],
          [
            33,
            8,
            65,
            14
          ],
          [
            37,
            0,
            14,
            69
          ]
        ],
        "directed_confusions": {
          "T2->T3": {
            "count": 14,
            "denominator": 120,
            "rate": 0.11666666666666667
          },
          "T3->T2": {
            "count": 8,
            "denominator": 120,
            "rate": 0.06666666666666667
          },
          "T3->T4": {
            "count": 14,
            "denominator": 120,
            "rate": 0.11666666666666667
          },
          "T4->T3": {
            "count": 14,
            "denominator": 120,
            "rate": 0.11666666666666667
          }
        }
      },
      "paired_correctness": {
        "both_correct": 202,
        "A_only_correct": 59,
        "B_only_correct": 43,
        "both_wrong": 176
      },
      "difference_B_minus_A": {
        "accuracy": -0.03333333333333333,
        "balanced_accuracy": -0.03333333333333333,
        "macro_f1": -0.03465117886272476,
        "per_tone": {
          "1": {
            "precision": -0.07463279078999603,
            "recall": 0.058333333333333334,
            "f1": -0.04197320529698753
          },
          "2": {
            "precision": -0.04499274310595065,
            "recall": -0.09166666666666666,
            "f1": -0.10273748500381721
          },
          "3": {
            "precision": 0.03231542801079225,
            "recall": -0.175,
            "f1": -0.0645109082669774
          },
          "4": {
            "precision": 0.06346153846153846,
            "recall": 0.075,
            "f1": 0.07061688311688312
          }
        }
      }
    }
  },
  "decision": {
    "promising": false,
    "checks": [
      {
        "condition": "pooled_accuracy_non_regression",
        "passed": false,
        "details": {
          "difference": -0.041666666666666664
        }
      },
      {
        "condition": "pooled_balanced_accuracy_non_regression",
        "passed": false,
        "details": {
          "difference": -0.041666666666666664
        }
      },
      {
        "condition": "pooled_macro_f1_non_regression",
        "passed": false,
        "details": {
          "difference": -0.041400568813010775
        }
      },
      {
        "condition": "strict_pooled_improvement",
        "passed": false,
        "details": {}
      },
      {
        "condition": "equal_speaker_mean_ba_non_regression",
        "passed": false,
        "details": {
          "difference": -0.041666666666666664
        }
      },
      {
        "condition": "tone_precision_drop_at_most_0.05",
        "passed": false,
        "details": {
          "violations": {
            "1": 0.12069904742274112,
            "2": 0.0625
          }
        }
      },
      {
        "condition": "tone_recall_drop_at_most_0.05",
        "passed": false,
        "details": {
          "violations": {
            "2": 0.07777777777777778,
            "3": 0.18333333333333332
          }
        }
      },
      {
        "condition": "tone_f1_drop_at_most_0.05",
        "passed": false,
        "details": {
          "violations": {
            "1": 0.0653787789761957,
            "2": 0.08932496075353218,
            "3": 0.059758888652331275
          }
        }
      },
      {
        "condition": "speaker_ba_drop_at_most_0.10",
        "passed": false,
        "details": {
          "violations": {
            "sait-ema:A_F001": 0.2,
            "sait-ema:L_F003": 0.175,
            "sait-ema:L_M002": 0.125,
            "sait-ema:M002": 0.15
          }
        }
      }
    ],
    "failed_conditions": [
      "pooled_accuracy_non_regression",
      "pooled_balanced_accuracy_non_regression",
      "pooled_macro_f1_non_regression",
      "strict_pooled_improvement",
      "equal_speaker_mean_ba_non_regression",
      "tone_precision_drop_at_most_0.05",
      "tone_recall_drop_at_most_0.05",
      "tone_f1_drop_at_most_0.05",
      "speaker_ba_drop_at_most_0.10"
    ],
    "interpretation": "Apply all nine conditions to the full panel; inspect complete metric differences for mixed, unchanged or worse behavior. Failure alone does not mean worse."
  }
}
```

Paired speaker-bootstrap percentile 95% intervals:

```json
{
  "accuracy": [
    -0.0805555555555556,
    -0.004166666666666652
  ],
  "balanced_accuracy": [
    -0.08055555555555566,
    -0.004166666666666652
  ],
  "macro_f1": [
    -0.08630229130326426,
    4.856854051720781e-05
  ],
  "equal_speaker_mean_balanced_accuracy": [
    -0.08055555555555566,
    -0.004166666666666541
  ]
}
```
