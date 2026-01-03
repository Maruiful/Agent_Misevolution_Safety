package com.agent.misevolution.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 暂停实验请求
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PauseExperimentRequest {

    /**
     * 实验 UUID
     */
    private String experimentUuid;
}
